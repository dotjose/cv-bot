"""Load structured website copy from ``data/website.json`` (no network I/O)."""

from __future__ import annotations

import asyncio
import json

from rag.chunking import WebsitePage

from app.core.config import Settings

_cache: tuple[float, list[WebsitePage]] | None = None
_cache_path: str | None = None


async def load_website_pages(settings: Settings) -> list[WebsitePage]:
    global _cache, _cache_path
    path = settings.data_dir / "website.json"
    key = str(path.resolve())
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return []

    if _cache is not None and _cache_path == key and _cache[0] == mtime:
        return _cache[1]

    def read() -> list[WebsitePage]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        pages = raw.get("pages") or []
        out: list[WebsitePage] = []
        for p in pages:
            if not isinstance(p, dict):
                continue
            url = str(p.get("url") or "")
            text = str(p.get("text") or "")
            if not url and not text:
                continue
            out.append(
                WebsitePage(
                    url=url,
                    title=p.get("title"),
                    text=text,
                )
            )
        return out

    pages = await asyncio.to_thread(read)
    _cache = (mtime, pages)
    _cache_path = key
    return pages


def format_website_projects_for_prompt(pages: list[WebsitePage], max_chars: int) -> str:
    if not pages:
        return "(No website.json pages.)"
    parts: list[str] = []
    n = 0
    for p in pages:
        header = f"### {p.title or p.url}\n{p.url}\n"
        block = header + p.text.strip()
        if n + len(block) > max_chars:
            remain = max(0, max_chars - n)
            if remain > 100:
                parts.append(block[:remain] + "\n…[truncated]")
            break
        parts.append(block)
        n += len(block) + 2
    return "\n\n---\n\n".join(parts) if parts else "(Empty website pages.)"
