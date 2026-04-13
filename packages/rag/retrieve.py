"""
Qdrant vector retrieval — scoring/dedup unchanged (collection ``cv_bot_chunks``).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from rag.types import ChunkType, RetrievedContext

logger = logging.getLogger(__name__)

COLLECTION_NAME = "cv_bot_chunks"

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


async def retrieve_for_query(
    settings: RagSettings,
    query_vector: list[float],
    query_text: str,
    *,
    top_k: int | None = None,
    prefetch: int | None = None,
) -> list[RetrievedContext]:
    prefetch = prefetch if prefetch is not None else settings.rag_prefetch
    top_k = top_k if top_k is not None else settings.rag_top_k
    weights = query_intent_weights(query_text)
    kwargs: dict[str, Any] = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key
    client = AsyncQdrantClient(**kwargs)
    try:
        try:
            # qdrant-client 1.17+ removed ``search`` on async client; use ``query_points``.
            res = await client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=prefetch,
                with_payload=True,
            )
        except UnexpectedResponse as e:
            if e.status_code == 404:
                body = (e.content or b"").decode("utf-8", errors="replace")
                if COLLECTION_NAME in body and (
                    "doesn't exist" in body or "not found" in body.lower()
                ):
                    logger.warning(
                        "Qdrant collection %r is missing; RAG disabled. "
                        "From apps/backend run: uv run python -m app.ingest_cli",
                        COLLECTION_NAME,
                    )
                    return []
            raise
    finally:
        await client.close()

    scored: list[RetrievedContext] = []
    for hit in res.points or []:
        p = hit.payload or {}
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
