import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file_paths() -> tuple[str, ...]:
    """Load `.env` from monorepo root first, then `apps/backend` (later wins). Fixes cwd-only `.env` when running uvicorn from `apps/backend`."""
    here = Path(__file__).resolve()
    candidates = (
        here.parents[4] / ".env",  # cv-bot (or repo root) / .env
        here.parents[2] / ".env",  # apps/backend/.env
    )
    found = tuple(str(p) for p in candidates if p.is_file())
    return found if found else (".env",)


def _default_data_dir() -> Path:
    if raw := os.environ.get("DATA_DIR"):
        return Path(raw)
    here = Path(__file__).resolve()
    monorepo = here.parents[4] / "data"
    if monorepo.is_dir():
        return monorepo
    # Lambda layout: /var/task/app/core/config.py → /var/task/data
    return here.parents[2] / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file_paths(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=_default_data_dir)

    openrouter_api_key: str = Field(validation_alias="OPENROUTER_API_KEY")
    openrouter_site_url: Optional[str] = Field(default=None, validation_alias="OPENROUTER_SITE_URL")
    openrouter_site_name: str = Field(default="cv-bot", validation_alias="OPENROUTER_SITE_NAME")
    openrouter_embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        validation_alias="OPENROUTER_EMBEDDING_MODEL",
    )
    openrouter_chat_model: str = Field(
        default="openai/gpt-4o-mini",
        validation_alias="OPENROUTER_CHAT_MODEL",
    )
    openrouter_max_retries: int = Field(default=3, validation_alias="OPENROUTER_MAX_RETRIES")
    openrouter_retry_base_ms: int = Field(default=400, validation_alias="OPENROUTER_RETRY_BASE_MS")

    qdrant_url: str = Field(validation_alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, validation_alias="QDRANT_API_KEY")
    qdrant_vector_size: int = Field(default=1536, validation_alias="QDRANT_VECTOR_SIZE")

    rag_top_k: int = Field(default=6, validation_alias="RAG_TOP_K")
    rag_prefetch: int = Field(default=24, validation_alias="RAG_PREFETCH")

    cors_origin: str = Field(default="*", validation_alias="CORS_ORIGIN")

    profile_data_path: Optional[Path] = Field(default=None, validation_alias="PROFILE_DATA_PATH")

    profile_identity_name: str = Field(default="Eyosiyas Tadele", validation_alias="PROFILE_IDENTITY_NAME")

    chat_s3_bucket: Optional[str] = Field(default=None, validation_alias="CHAT_S3_BUCKET")
    chat_s3_prefix: str = Field(default="chat/", validation_alias="CHAT_S3_PREFIX")
    aws_region: Optional[str] = Field(default=None, validation_alias="AWS_REGION")
    chat_session_header: str = Field(default="X-Session-Id", validation_alias="CHAT_SESSION_HEADER")

    prompt_max_source_chars: int = Field(default=8000, validation_alias="PROMPT_MAX_SOURCE_CHARS")

    @field_validator("data_dir", mode="before")
    @classmethod
    def _coerce_data_dir(cls, v: object) -> Path:
        if v is None or v == "":
            return _default_data_dir()
        return Path(v) if not isinstance(v, Path) else v


@lru_cache
def get_settings() -> Settings:
    return Settings()
