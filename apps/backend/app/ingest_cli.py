"""
Chunk ``data/`` sources, embed via OpenRouter, upsert Qdrant.

Run from ``apps/backend/``::

    uv run python -m app.ingest_cli
"""

from __future__ import annotations

import app._monorepo_path  # noqa: F401

import asyncio
import hashlib
import sys
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from rag.chunking import RagChunkPayload, chunk_plain_text, chunk_website_pages
from rag.retrieve import COLLECTION_NAME

from app.core.config import Settings, get_settings
from app.services import document_service, llm_openrouter, website_scraper

BATCH = 32


def stable_point_id(parts: list[str]) -> str:
    hex_d = hashlib.sha256("\0".join(parts).encode()).hexdigest()[:32]
    return f"{hex_d[:8]}-{hex_d[8:12]}-{hex_d[12:16]}-{hex_d[16:20]}-{hex_d[20:32]}"


def _ensure_collection(client: QdrantClient, settings: Settings) -> None:
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        return
    except Exception:
        pass
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=settings.qdrant_vector_size, distance=Distance.COSINE),
    )


async def _run() -> None:
    settings = get_settings()
    kwargs: dict[str, Any] = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key
    client = QdrantClient(**kwargs)
    try:
        _ensure_collection(client, settings)

        cv_text, li_text, summary_raw, pages = await asyncio.gather(
            document_service.load_cv_text(settings),
            document_service.load_linkedin_text(settings),
            document_service.load_summary_text(settings),
            website_scraper.load_website_pages(settings),
        )

        chunks: list[RagChunkPayload] = [
            *chunk_plain_text(cv_text, "cv", "experience"),
            *chunk_plain_text(li_text, "linkedin", "experience"),
            *chunk_plain_text(summary_raw, "summary", "summary"),
            *chunk_website_pages(pages),
        ]
        chunks = [c for c in chunks if len(c["text"].strip()) > 20]

        if not chunks:
            print("No chunks produced — check data/ files.", file=sys.stderr)
            raise SystemExit(1)

        print(f"Embedding {len(chunks)} chunks…", file=sys.stderr)

        timeout = httpx.Timeout(300.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as http:
            points: list[PointStruct] = []
            for i in range(0, len(chunks), BATCH):
                slice_ = chunks[i : i + BATCH]
                vectors = await llm_openrouter.embed_texts(
                    http, settings, [c["text"] for c in slice_], "document"
                )
                for j, c in enumerate(slice_):
                    pid = stable_point_id([c["source"], c["type"], c["text"]])
                    vec = vectors[j] if j < len(vectors) else None
                    if not vec:
                        continue
                    points.append(
                        PointStruct(
                            id=pid,
                            vector=vec,
                            payload={
                                "type": c["type"],
                                "source": c["source"],
                                "text": c["text"],
                                "title": c.get("title"),
                            },
                        )
                    )

            if not points:
                print("No vectors produced.", file=sys.stderr)
                raise SystemExit(1)

            client.upsert(collection_name=COLLECTION_NAME, wait=True, points=points)
            print(f"Upserted {len(points)} points to {COLLECTION_NAME}.", file=sys.stderr)
    finally:
        client.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
