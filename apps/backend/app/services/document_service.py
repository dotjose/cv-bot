"""Load CV and LinkedIn text from data/ (PDF or .txt fallback). Read-only, async."""

from __future__ import annotations

import asyncio
from pathlib import Path

from pypdf import PdfReader

from app.core.config import Settings
from app.utils.logger import log

_cache: dict[str, tuple[float, str]] = {}


def _read_pdf_sync(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        parts.append(t)
    return "\n".join(parts).strip()


async def _cached_text(path: Path, loader) -> str:
    key = str(path.resolve())
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return ""
    hit = _cache.get(key)
    if hit and hit[0] == mtime:
        return hit[1]
    text = await asyncio.to_thread(loader, path)
    _cache[key] = (mtime, text)
    return text


async def load_pdf_or_text(settings: Settings, base_name: str) -> str:
    """Load ``{data_dir}/{base}.pdf`` or fall back to ``{base}.txt``."""
    data = settings.data_dir
    pdf_path = data / f"{base_name}.pdf"
    txt_path = data / f"{base_name}.txt"

    async def load_pdf(p: Path) -> str:
        try:
            return await _cached_text(p, lambda path: _read_pdf_sync(path))
        except Exception as e:  # noqa: BLE001
            log.warning("PDF read failed %s: %s", p, e)
            return ""

    if pdf_path.is_file():
        body = await load_pdf(pdf_path)
        if body.strip():
            return body
    if txt_path.is_file():

        def read_txt(p: Path) -> str:
            return p.read_text(encoding="utf-8")

        return await _cached_text(txt_path, read_txt)
    return ""


async def load_cv_text(settings: Settings) -> str:
    return await load_pdf_or_text(settings, "cv")


async def load_linkedin_text(settings: Settings) -> str:
    return await load_pdf_or_text(settings, "linkedin")


async def load_summary_text(settings: Settings) -> str:
    p = settings.data_dir / "summary.txt"
    if not p.is_file():
        return ""

    def read_txt(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    return await _cached_text(p, read_txt)
