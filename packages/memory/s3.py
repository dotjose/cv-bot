"""S3 chat session storage — one JSON object per session (envelope + legacy array support)."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Protocol

import aioboto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class ChatMemorySettings(Protocol):
    chat_s3_bucket: str | None
    chat_s3_prefix: str
    aws_region: str | None


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_prefix(prefix: str) -> str:
    p = (prefix or "chat/").strip()
    return p if p.endswith("/") else f"{p}/"


def object_key(settings: ChatMemorySettings, session_id: str) -> str:
    sid = session_id.strip()
    return f"{normalize_prefix(settings.chat_s3_prefix)}{sid}.json"


def _coerce_message(m: Any) -> dict[str, str] | None:
    if not isinstance(m, dict):
        return None
    r, c = m.get("role"), m.get("content")
    if r not in ("user", "assistant") or not isinstance(c, str):
        return None
    ts = m.get("timestamp")
    out: dict[str, str] = {"role": r, "content": c}
    if isinstance(ts, str) and ts.strip():
        out["timestamp"] = ts.strip()
    else:
        out["timestamp"] = utc_iso()
    return out


def parse_stored_session(session_id: str, data: Any) -> dict[str, Any]:
    """Normalize S3 body to ``{session_id, created_at, messages}``."""
    if isinstance(data, list):
        msgs = []
        for m in data:
            cm = _coerce_message(m)
            if cm:
                msgs.append(cm)
        return {"session_id": session_id, "created_at": utc_iso(), "messages": msgs}

    if isinstance(data, dict) and isinstance(data.get("messages"), list):
        sid = str(data.get("session_id") or session_id)
        ca = data.get("created_at")
        ca_out = str(ca) if isinstance(ca, str) and ca.strip() else utc_iso()
        msgs: list[dict[str, str]] = []
        for m in data["messages"]:
            cm = _coerce_message(m)
            if cm:
                msgs.append(cm)
        return {"session_id": sid, "created_at": ca_out, "messages": msgs}

    return {"session_id": session_id, "created_at": utc_iso(), "messages": []}


async def _get_object_json(settings: ChatMemorySettings, key: str) -> Any | Literal["NOSUCHKEY"] | None:
    """``None`` = bucket not configured; ``NOSUCHKEY`` = missing object; else parsed JSON."""
    if not settings.chat_s3_bucket:
        return None
    session = aioboto3.Session()
    try:
        async with session.client("s3", region_name=settings.aws_region or None) as s3:
            resp = await s3.get_object(Bucket=settings.chat_s3_bucket, Key=key)
            body = await resp["Body"].read()
            return json.loads(body.decode("utf-8"))
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404"):
            return "NOSUCHKEY"
        log.warning("S3 get_object ClientError: %s", e)
        return "NOSUCHKEY"
    except Exception as e:  # noqa: BLE001
        log.warning("S3 get_object error: %s", e)
        return "NOSUCHKEY"


async def _put_object_json(settings: ChatMemorySettings, key: str, payload: dict[str, Any]) -> bool:
    if not settings.chat_s3_bucket:
        return False
    session = aioboto3.Session()
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        async with session.client("s3", region_name=settings.aws_region or None) as s3:
            await s3.put_object(
                Bucket=settings.chat_s3_bucket,
                Key=key,
                Body=raw,
                ContentType="application/json",
            )
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("S3 put_object error: %s", e)
        return False


async def load_chat(
    settings: ChatMemorySettings,
    session_id: str | None,
) -> list[dict[str, Any]] | None:
    """
    Messages for LLM turns: ``[{"role","content"}, ...]`` (no timestamps).

    Returns ``None`` if S3 is not configured (caller uses request body).
    Returns ``[]`` for a new / empty session key.
    """
    if not settings.chat_s3_bucket or not session_id or not session_id.strip():
        return None
    key = object_key(settings, session_id)
    raw = await _get_object_json(settings, key)
    if raw is None:
        return None
    if raw == "NOSUCHKEY":
        return []
    doc = parse_stored_session(session_id.strip(), raw)
    return [{"role": m["role"], "content": m["content"]} for m in doc["messages"]]


async def load_chat_messages_with_meta(
    settings: ChatMemorySettings,
    session_id: str | None,
) -> list[dict[str, Any]] | None:
    """Like ``load_chat`` but each item may include ``timestamp`` (for prompts / API)."""
    if not settings.chat_s3_bucket or not session_id or not session_id.strip():
        return None
    key = object_key(settings, session_id)
    raw = await _get_object_json(settings, key)
    if raw is None:
        return None
    if raw == "NOSUCHKEY":
        return []
    doc = parse_stored_session(session_id.strip(), raw)
    return list(doc["messages"])


async def get_session_document(
    settings: ChatMemorySettings,
    session_id: str,
) -> dict[str, Any] | None:
    """
    Full envelope for HTTP GET. Returns ``None`` if S3 disabled or object does not exist.
    """
    if not settings.chat_s3_bucket or not session_id.strip():
        return None
    key = object_key(settings, session_id)
    raw = await _get_object_json(settings, key)
    if raw is None or raw == "NOSUCHKEY":
        return None
    return parse_stored_session(session_id.strip(), raw)


async def save_chat(
    settings: ChatMemorySettings,
    session_id: str | None,
    messages: list[dict[str, Any]],
) -> None:
    """Persist ``messages`` as session envelope (adds timestamps where missing)."""
    if not settings.chat_s3_bucket or not session_id or not session_id.strip():
        return
    sid = session_id.strip()
    key = object_key(settings, sid)
    existing = await _get_object_json(settings, key)
    created_at = utc_iso()
    if existing not in (None, "NOSUCHKEY") and isinstance(existing, dict):
        ca = existing.get("created_at")
        if isinstance(ca, str) and ca.strip():
            created_at = ca.strip()
    elif existing not in (None, "NOSUCHKEY") and isinstance(existing, list):
        created_at = utc_iso()

    norm_msgs: list[dict[str, str]] = []
    for m in messages:
        cm = _coerce_message(m)
        if cm:
            norm_msgs.append(cm)

    envelope: dict[str, Any] = {
        "session_id": sid,
        "created_at": created_at,
        "messages": norm_msgs,
    }
    await _put_object_json(settings, key, envelope)


async def create_empty_session(settings: ChatMemorySettings) -> str | None:
    """
    Allocate a new session id and write an empty envelope to S3.
    Returns ``None`` if bucket not configured (caller may still mint a client-only id).
    """
    if not settings.chat_s3_bucket:
        return None
    sid = str(uuid.uuid4())
    envelope = {"session_id": sid, "created_at": utc_iso(), "messages": []}
    ok = await _put_object_json(settings, object_key(settings, sid), envelope)
    return sid if ok else None


async def list_sessions(
    settings: ChatMemorySettings,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List recent session objects under ``CHAT_S3_PREFIX`` (requires ``s3:ListBucket`` on deploy).
    Each item: ``session_id``, ``updated_at`` (object LastModified ISO).
    """
    if not settings.chat_s3_bucket:
        return []
    prefix = normalize_prefix(settings.chat_s3_prefix)
    session = aioboto3.Session()
    out: list[dict[str, Any]] = []
    try:
        async with session.client("s3", region_name=settings.aws_region or None) as s3:
            resp = await s3.list_objects_v2(
                Bucket=settings.chat_s3_bucket,
                Prefix=prefix,
                MaxKeys=min(limit * 2, 1000),
            )
        contents = list(resp.get("Contents") or [])
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)

        def _sort_key(x: dict[str, Any]) -> datetime:
            lm = x.get("LastModified")
            return lm if isinstance(lm, datetime) else epoch

        contents.sort(key=_sort_key, reverse=True)
        for obj in contents:
            if len(out) >= limit:
                break
            key = obj.get("Key") or ""
            if not key.endswith(".json"):
                continue
            if not key.startswith(prefix):
                continue
            sid = key[len(prefix) : -len(".json")]
            if not sid:
                continue
            lm = obj.get("LastModified")
            updated = lm.isoformat() if hasattr(lm, "isoformat") else utc_iso()
            out.append({"session_id": sid, "updated_at": updated})
    except Exception as e:  # noqa: BLE001
        log.warning("list_sessions error: %s", e)
    return out
