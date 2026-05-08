"""
Qdrant vector retrieval — scoring/dedup unchanged (collection ``cv_bot_chunks``).
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Protocol

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from rag.types import ChunkType, RetrievedContext

logger = logging.getLogger(__name__)

COLLECTION_NAME = "cv_bot_chunks"
DEFAULT_QDRANT_TIMEOUT_S = 6.0

# Truth priority when blending vector score with source (website > cv > linkedin > summary).
SOURCE_TRUTH_WEIGHT: dict[str, float] = {
    "website": 1.22,
    "cv": 1.12,
    "linkedin": 1.06,
    "summary": 1.0,
}


class RagSettings(Protocol):
    qdrant_url: str
    qdrant_api_key: str | None
    rag_top_k: int
    rag_prefetch: int


INTENT = {
    "intro": re.compile(
        r"yourself|who are you|introduce|background|overview|tell me about|founder|co-?found|startup|habesha",
        re.I,
    ),
    "technical": re.compile(
        r"skill|stack|tech|language|framework|library|typescript|javascript|python|react|node|nest(?:js)?|"
        r"aws|docker|kubernetes|sql|api|kafka|redis|graphql|grpc|microservice|event|stream|fintech|blockchain|"
        r"llm|openai|ai integration",
        re.I,
    ),
    "experience": re.compile(
        r"work|job|company|role|employ|experience|career|previous|where did you|lead|mentor|architect",
        re.I,
    ),
    "education": re.compile(
        r"education|degree|university|college|study|studied|school|graduat",
        re.I,
    ),
}


def query_intent_weights(query: str) -> dict[ChunkType, float]:
    q = query.strip()
    w: dict[ChunkType, float] = {
        "project": 1.0,
        "skill": 1.0,
        "experience": 1.0,
        "summary": 1.0,
    }
    if INTENT["intro"].search(q):
        w["project"] *= 1.45
        w["summary"] *= 1.35
    if INTENT["technical"].search(q):
        w["skill"] *= 1.5
        w["project"] *= 1.15
    if INTENT["experience"].search(q):
        w["experience"] *= 1.5
        w["summary"] *= 1.1
    if INTENT["education"].search(q):
        w["summary"] *= 1.35
        w["experience"] *= 1.12
    return w


def _select_diverse(
    scored: list[RetrievedContext],
    top_k: int,
    *,
    max_per_type: int = 3,
    prefix_len: int = 160,
) -> list[RetrievedContext]:
    """Prefer a mix of chunk types; fill remaining slots by pure score after caps."""
    seen: set[str] = set()
    type_counts: dict[str, int] = {}
    out: list[RetrievedContext] = []

    def dedupe_key(row: RetrievedContext) -> str:
        return f"{row.type}:{row.text[:prefix_len].strip().lower()}"

    for row in scored:
        k = dedupe_key(row)
        if k in seen:
            continue
        if type_counts.get(row.type, 0) >= max_per_type:
            continue
        seen.add(k)
        type_counts[row.type] = type_counts.get(row.type, 0) + 1
        out.append(row)
        if len(out) >= top_k:
            return out

    for row in scored:
        k = dedupe_key(row)
        if k in seen:
            continue
        seen.add(k)
        out.append(row)
        if len(out) >= top_k:
            break
    return out


def _safe_log_warning(
    msg: str,
    *,
    request_id: str | None,
    query: str | None,
    failure_reason: str,
    collection_name: str = COLLECTION_NAME,
) -> None:
    # Keep logs concise and CloudWatch-friendly (avoid stack traces for expected failures).
    logger.warning(
        "%s collection=%s request_id=%s query=%s reason=%s",
        msg,
        collection_name,
        request_id or "",
        (query or "")[:240],
        failure_reason,
    )


def _is_valid_vector(v: list[float]) -> bool:
    if not v:
        return False
    # Defensive: ensure floats are finite. (NaN/Inf can crash or yield undefined behavior server-side.)
    for x in v:
        try:
            xf = float(x)
        except Exception:
            return False
        if not math.isfinite(xf):
            return False
    return True


def _qdrant_kwargs(settings: RagSettings, *, timeout_s: float) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "url": (settings.qdrant_url or "").strip(),
        "timeout": timeout_s,
        # Avoid extra round-trips on cold starts and noisy warnings when a proxy blocks version endpoints.
        "check_compatibility": False,
    }
    if settings.qdrant_api_key and settings.qdrant_api_key.strip():
        kwargs["api_key"] = settings.qdrant_api_key.strip()
    return kwargs


async def retrieve_for_query(
    settings: RagSettings,
    query_vector: list[float],
    query_text: str,
    *,
    top_k: int | None = None,
    prefetch: int | None = None,
    request_id: str | None = None,
    timeout_s: float = DEFAULT_QDRANT_TIMEOUT_S,
) -> list[RetrievedContext]:
    """
    Production-safe retrieval:
    - Never raises (returns [] on any failure)
    - Uses official AsyncQdrantClient only (no raw REST fallbacks)
    - Tight timeouts to avoid Lambda tail latency
    """
    q = (query_text or "").strip()

    # Config validation (non-fatal).
    if not (settings.qdrant_url or "").strip():
        _safe_log_warning(
            "Qdrant disabled (missing QDRANT_URL)",
            request_id=request_id,
            query=q,
            failure_reason="missing_qdrant_url",
        )
        return []
    if not (settings.qdrant_api_key or "").strip():
        # Some local deployments may not need an API key; keep it as a warning.
        _safe_log_warning(
            "Qdrant API key missing; retrieval may fail",
            request_id=request_id,
            query=q,
            failure_reason="missing_qdrant_api_key",
        )

    # Input validation (non-fatal).
    if not q:
        return []
    if not _is_valid_vector(query_vector):
        _safe_log_warning(
            "Invalid query vector; continuing without RAG",
            request_id=request_id,
            query=q,
            failure_reason="invalid_vector",
        )
        return []

    prefetch = int(prefetch if prefetch is not None else settings.rag_prefetch)
    top_k = int(top_k if top_k is not None else settings.rag_top_k)
    if prefetch <= 0 or top_k <= 0:
        return []

    weights = query_intent_weights(q)
    client = AsyncQdrantClient(**_qdrant_kwargs(settings, timeout_s=timeout_s))
    try:
        try:  # Never allow retrieval to raise past this function.
            # qdrant-client 1.17+ removed ``search`` on async client; use ``query_points``.
            res = await client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=prefetch,
                with_payload=True,
            )
        except UnexpectedResponse as e:
            # Expected operational failures: collection missing, route not available, auth issues, etc.
            reason = f"unexpected_response_{e.status_code}"
            if e.status_code == 404:
                body = (e.content or b"").decode("utf-8", errors="replace").strip().lower()
                if "doesn't exist" in body or "does not exist" in body or "not found" == body:
                    _safe_log_warning(
                        "Qdrant collection missing; continuing without RAG",
                        request_id=request_id,
                        query=q,
                        failure_reason="collection_missing",
                    )
                    return []
                # Common proxy response when endpoint is blocked/misrouted.
                if body == "404 page not found":
                    _safe_log_warning(
                        "Qdrant endpoint not found; continuing without RAG",
                        request_id=request_id,
                        query=q,
                        failure_reason="qdrant_endpoint_404",
                    )
                    return []
            _safe_log_warning(
                "Qdrant query failed; continuing without RAG",
                request_id=request_id,
                query=q,
                failure_reason=reason,
            )
            return []
        except Exception as exc:
            _safe_log_warning(
                "Qdrant query exception; continuing without RAG",
                request_id=request_id,
                query=q,
                failure_reason=exc.__class__.__name__,
            )
            return []
    finally:
        try:
            await client.close()
        except Exception:
            # Never allow cleanup failures to cascade.
            pass

    scored: list[RetrievedContext] = []
    for hit in res.points or []:
        p_raw = hit.payload
        if p_raw is None:
            continue
        if not isinstance(p_raw, dict):
            continue
        p: dict[str, Any] = p_raw
        ctype = p.get("type")
        if ctype not in ("project", "skill", "experience", "summary"):
            continue
        raw_src = p.get("source")
        src = (
            raw_src
            if raw_src in ("cv", "linkedin", "website", "summary")
            else "summary"
        )
        base = float(hit.score or 0)
        src_weight = SOURCE_TRUTH_WEIGHT.get(src, 1.0)
        adjusted = base * weights.get(ctype, 1.0) * src_weight
        scored.append(
            RetrievedContext(
                id=str(hit.id),
                score=adjusted,
                type=ctype,
                source=src,
                text=str(p.get("text", "")),
                title=p.get("title"),
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    return _select_diverse(scored, top_k)
