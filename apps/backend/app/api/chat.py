import uuid

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

import memory.s3 as memory_s3
from app.core.config import get_settings
from app.models.schemas import (
    ChatRequestBody,
    ChatSessionCreateResponse,
    ChatSessionEnvelope,
    ChatSessionListResponse,
    ChatSessionSummary,
    StoredChatMessage,
)
from app.services import chat_service
from app.services.profile_store import clear_profile_cache

router = APIRouter(tags=["chat"])


def _session_id(request: Request) -> str | None:
    settings = get_settings()
    return request.headers.get(settings.chat_session_header)


@router.post("/chat/reset")
async def chat_reset() -> dict[str, bool]:
    clear_profile_cache()
    return {"ok": True}


@router.post("/chat/sessions", status_code=201, response_model=ChatSessionCreateResponse)
async def create_chat_session() -> ChatSessionCreateResponse:
    """Create a new empty session in S3 (or mint a UUID if ``CHAT_S3_BUCKET`` is unset)."""
    settings = get_settings()
    sid = await memory_s3.create_empty_session(settings)
    if not sid:
        sid = str(uuid.uuid4())
    return ChatSessionCreateResponse(session_id=sid)


@router.get("/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions() -> ChatSessionListResponse:
    settings = get_settings()
    rows = await memory_s3.list_sessions(settings, limit=50)
    return ChatSessionListResponse(
        sessions=[ChatSessionSummary(session_id=r["session_id"], updated_at=r["updated_at"]) for r in rows]
    )


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionEnvelope)
async def get_chat_session(session_id: str) -> ChatSessionEnvelope:
    settings = get_settings()
    doc = await memory_s3.get_session_document(settings, session_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Session not found or chat storage not configured")
    msgs_raw = doc.get("messages") or []
    messages: list[StoredChatMessage] = []
    for m in msgs_raw:
        if not isinstance(m, dict):
            continue
        r, c = m.get("role"), m.get("content")
        ts = m.get("timestamp")
        if r in ("user", "assistant") and isinstance(c, str) and isinstance(ts, str) and ts.strip():
            messages.append(StoredChatMessage(role=r, content=c, timestamp=ts.strip()))
        elif r in ("user", "assistant") and isinstance(c, str):
            messages.append(StoredChatMessage(role=r, content=c, timestamp=memory_s3.utc_iso()))
    return ChatSessionEnvelope(
        session_id=str(doc["session_id"]),
        created_at=str(doc.get("created_at") or memory_s3.utc_iso()),
        messages=messages,
    )


@router.post("/chat")
async def chat(request: Request, body: ChatRequestBody) -> StreamingResponse:
    settings = get_settings()
    msg = body.message.strip()
    if not msg:
        return JSONResponse(status_code=400, content={"error": "message is required"})

    http_client: httpx.AsyncClient = request.app.state.http
    sid = _session_id(request)

    try:
        ctx = await chat_service.build_chat_context(settings, http_client, body, sid)
    except RuntimeError as e:
        if str(e) == "Embedding failed":
            return JSONResponse(status_code=502, content={"error": "Embedding failed"})
        raise

    async def gen():
        async for chunk in chat_service.stream_llm_sse(settings, http_client, ctx):
            yield chunk

    return StreamingResponse(
        gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
