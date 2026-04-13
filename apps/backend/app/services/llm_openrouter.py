"""
OpenRouter-only LLM gateway (async httpx). Retries on transient failures (429, 5xx, timeouts).
"""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import Settings
from app.utils.logger import log

OPENROUTER_URL = "https://openrouter.ai/api/v1"


def _headers(settings: Settings) -> dict[str, str]:
    h: dict[str, str] = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_site_url:
        h["HTTP-Referer"] = settings.openrouter_site_url
    h["X-Title"] = settings.openrouter_site_name
    return h


def _retryable_status(code: int) -> bool:
    return code == 429 or code >= 500


async def _sleep_attempt(attempt: int, base_ms: int) -> None:
    await asyncio.sleep(min(base_ms * (2**attempt) / 1000.0, 8.0))


async def embed_texts(
    client: httpx.AsyncClient,
    settings: Settings,
    inputs: list[str],
    input_type: str | None = None,
) -> list[list[float]]:
    if not inputs:
        return []
    body: dict[str, Any] = {
        "model": settings.openrouter_embedding_model,
        "input": inputs,
        "encoding_format": "float",
    }
    if input_type:
        body["input_type"] = "search_query" if input_type == "query" else "search_document"

    last_err: str | None = None
    for attempt in range(settings.openrouter_max_retries + 1):
        try:
            res = await client.post(
                f"{OPENROUTER_URL}/embeddings",
                headers=_headers(settings),
                json=body,
                timeout=120.0,
            )
            if res.status_code == 200:
                data = res.json()
                rows = sorted(data["data"], key=lambda x: x["index"])
                return [r["embedding"] for r in rows]
            last_err = f"{res.status_code} {res.text}"
            if not _retryable_status(res.status_code) or attempt >= settings.openrouter_max_retries:
                break
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_err = str(e)
            if attempt >= settings.openrouter_max_retries:
                break
        log.warning("OpenRouter embeddings retry %s/%s", attempt + 1, settings.openrouter_max_retries)
        await _sleep_attempt(attempt, settings.openrouter_retry_base_ms)

    raise RuntimeError(f"OpenRouter embeddings failed: {last_err}")


async def stream_chat_completion(
    client: httpx.AsyncClient,
    settings: Settings,
    *,
    system: str,
    messages: list[dict],
    temperature: float = 0.25,
    max_tokens: int = 900,
) -> AsyncIterator[str]:
    body = {
        "model": settings.openrouter_chat_model,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, *messages],
    }

    last_err: str | None = None
    for attempt in range(settings.openrouter_max_retries + 1):
        try:
            async with client.stream(
                "POST",
                f"{OPENROUTER_URL}/chat/completions",
                headers=_headers(settings),
                json=body,
                timeout=300.0,
            ) as res:
                if res.status_code != 200:
                    err = (await res.aread()).decode()
                    last_err = f"{res.status_code} {err}"
                    if _retryable_status(res.status_code) and attempt < settings.openrouter_max_retries:
                        log.warning("OpenRouter chat retry %s/%s", attempt + 1, settings.openrouter_max_retries)
                        await _sleep_attempt(attempt, settings.openrouter_retry_base_ms)
                        continue
                    raise RuntimeError(f"OpenRouter chat failed: {last_err}")

                async for line in res.aiter_lines():
                    trimmed = line.strip()
                    if not trimmed.startswith("data:"):
                        continue
                    payload = trimmed[5:].strip()
                    if payload == "[DONE]":
                        return
                    try:
                        j = json.loads(payload)
                        content = (j.get("choices") or [{}])[0].get("delta", {}).get("content")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
                return
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_err = str(e)
            if attempt >= settings.openrouter_max_retries:
                raise RuntimeError(f"OpenRouter chat failed: {last_err}") from e
            log.warning("OpenRouter chat transport retry %s/%s", attempt + 1, settings.openrouter_max_retries)
            await _sleep_attempt(attempt, settings.openrouter_retry_base_ms)

    raise RuntimeError(f"OpenRouter chat failed: {last_err or 'unknown'}")


async def sse_from_text_stream(source: AsyncIterator[str]) -> AsyncIterator[bytes]:
    async for chunk in source:
        line = json.dumps({"text": chunk})
        yield f"data: {line}\n\n".encode("utf-8")
    yield b"data: [DONE]\n\n"
