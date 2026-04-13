import app._monorepo_path  # noqa: F401 — register ``packages/`` before shared imports

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, profile
from app.core.config import get_settings
from app.utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0))
    log.info("httpx AsyncClient ready")
    yield
    await app.state.http.aclose()
    log.info("httpx AsyncClient closed")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CV Bot API", lifespan=lifespan)

    origins = ["*"] if settings.cors_origin.strip() == "*" else [settings.cors_origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
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
