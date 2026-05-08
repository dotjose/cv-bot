import app._monorepo_path  # noqa: F401 — register ``packages/`` before shared imports

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, profile
from app.core.config import get_settings
from app.utils.logger import log
from rag.retrieve import COLLECTION_NAME


async def _validate_qdrant_startup(settings) -> None:
    """
    Best-effort startup validation. Never raises.
    Validates:
    - QDRANT_URL present
    - QDRANT_API_KEY present (warn only; local may omit)
    - Collection exists (warn only)
    """
    try:
        from qdrant_client import AsyncQdrantClient
    except Exception as exc:
        log.warning("Qdrant client import failed; RAG disabled reason=%s", exc.__class__.__name__)
        return

    url = (getattr(settings, "qdrant_url", "") or "").strip()
    key = (getattr(settings, "qdrant_api_key", "") or "").strip()
    if not url:
        log.warning("Qdrant disabled (missing QDRANT_URL)")
        return
    if not key:
        log.warning("Qdrant API key missing; retrieval may fail")

    client = AsyncQdrantClient(url=url, api_key=key or None, timeout=3.5, check_compatibility=False)
    try:
        try:
            await client.get_collection(collection_name=COLLECTION_NAME)
            log.info("Qdrant collection ready collection=%s", COLLECTION_NAME)
        except Exception as exc:
            # Don't crash startup if collection is missing/outage.
            log.warning(
                "Qdrant collection not ready; RAG will degrade collection=%s reason=%s",
                COLLECTION_NAME,
                exc.__class__.__name__,
            )
    finally:
        try:
            await client.close()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0))
    log.info("httpx AsyncClient ready")
    # Best-effort Qdrant validation (never blocks startup).
    try:
        settings = get_settings()
        await _validate_qdrant_startup(settings)
    except Exception as exc:
        log.warning("Qdrant startup validation skipped reason=%s", exc.__class__.__name__)
    yield
    await app.state.http.aclose()
    log.info("httpx AsyncClient closed")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CV Bot API", lifespan=lifespan)

    # CORS: wildcard origin cannot use credentials=True (browser + Starlette rules). API Gateway also sets CORS.
    origins = ["*"] if settings.cors_origin.strip() == "*" else [settings.cors_origin.strip()]
    creds = origins != ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=creds,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"ok": True}

    app.include_router(chat.router)
    app.include_router(profile.router)
    return app


app = create_app()
# Lambda + API Gateway HTTP API (local dev: uvicorn `app.main:app`).
handler = Mangum(app, lifespan="on")
