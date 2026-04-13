"""
Chat orchestration: S3 → RAG → documents → skills → prompts → OpenRouter → S3.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import NamedTuple

import httpx
import memory.s3 as memory_s3
from prompts.builder import build_message_turns, build_system_prompt
from rag.retrieve import retrieve_for_query

from app.core.config import Settings
from app.models.schemas import ChatRequestBody
from app.services import document_service, llm_openrouter, profile_store, skill_extractor, website_scraper
from app.utils.logger import log


class ChatContext(NamedTuple):
    system: str
    turns: list[dict]
    message: str
    history: list[dict]
    session_id: str | None


async def build_chat_context(
    settings: Settings,
    http: httpx.AsyncClient,
    body: ChatRequestBody,
    session_id: str | None,
) -> ChatContext:
    srv_hist = await memory_s3.load_chat_messages_with_meta(settings, session_id)
    if srv_hist is not None:
        history = list(srv_hist)
        log.debug("Using S3-backed history (%d turns)", len(history))
    else:
        history = [m.model_dump() for m in body.history]

    message = body.message.strip()
    vecs = await llm_openrouter.embed_texts(http, settings, [message], "query")
    if not vecs or not vecs[0]:
        raise RuntimeError("Embedding failed")

    retrieved = await retrieve_for_query(
        settings,
        vecs[0],
        message,
        top_k=settings.rag_top_k,
        prefetch=settings.rag_prefetch,
    )

    cv_text, linkedin_text, summary_text, pages, profile = await asyncio.gather(
        document_service.load_cv_text(settings),
        document_service.load_linkedin_text(settings),
        document_service.load_summary_text(settings),
        website_scraper.load_website_pages(settings),
        profile_store.load_dynamic_profile(settings),
    )
    dynamic_block = profile_store.overview_prompt_block(
        profile.get("overview"),
        max_chars=min(2800, max(800, settings.prompt_max_source_chars // 3)),
    )
    website_blob = website_scraper.format_website_projects_for_prompt(
        pages, settings.prompt_max_source_chars
    )
    skills = await skill_extractor.extract_skills(
        settings, cv_text=cv_text, linkedin_text=linkedin_text
    )

    system = build_system_prompt(
        identity_name=settings.profile_identity_name,
        cv_text=cv_text,
        linkedin_text=linkedin_text,
        summary_text=summary_text,
        website_projects=website_blob,
        skills=skills,
        rag_context=retrieved,
        chat_history=history,
        max_source_chars=settings.prompt_max_source_chars,
        dynamic_profile_block=dynamic_block,
        contact_block=profile_store.canonical_contact_prompt_block(),
    )
    turns = build_message_turns(history, message)
    return ChatContext(system=system, turns=turns, message=message, history=history, session_id=session_id)


async def stream_llm_sse(
    settings: Settings,
    http: httpx.AsyncClient,
    ctx: ChatContext,
) -> AsyncIterator[bytes]:
    acc: list[str] = []

    async def text_stream() -> AsyncIterator[str]:
        async for delta in llm_openrouter.stream_chat_completion(
            http, settings, system=ctx.system, messages=ctx.turns
        ):
            acc.append(delta)
            yield delta

    async for chunk in llm_openrouter.sse_from_text_stream(text_stream()):
        yield chunk

    assistant_text = "".join(acc)
    if assistant_text.strip():
        to_save = [
            *ctx.history,
            {"role": "user", "content": ctx.message},
            {"role": "assistant", "content": assistant_text},
        ]
        await memory_s3.save_chat(settings, ctx.session_id, to_save)
