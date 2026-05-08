"""dynamic-profile.json load + cache (same behavior as the former Node profile loader)."""

import json
from pathlib import Path
from typing import Any, Optional

from app.core.config import Settings
from app.utils.logger import log

_cached: dict[str, Any] | None = None
_cached_path: str | None = None
_cached_mtime_ns: int | None = None


def _candidates(settings: Settings) -> list[Path]:
    out: list[Path] = []
    if settings.profile_data_path:
        out.append(Path(settings.profile_data_path))
    out.append(settings.data_dir / "dynamic-profile.json")
    # cwd variants (repo root vs apps)
    out.append(Path.cwd() / "data" / "dynamic-profile.json")
    out.append(Path.cwd() / ".." / ".." / "data" / "dynamic-profile.json")
    # relative to this file: backend/app/services -> ../../../data
    here = Path(__file__).resolve().parent
    out.append(here / ".." / ".." / ".." / "data" / "dynamic-profile.json")
    return out


async def resolve_profile_path(settings: Settings) -> Path:
    for p in _candidates(settings):
        try:
            rp = p.resolve()
            if rp.is_file():
                return rp
        except OSError:
            continue
    tried = ", ".join(str(p) for p in _candidates(settings))
    raise FileNotFoundError(f"dynamic-profile.json not found. Tried: {tried}. Set PROFILE_DATA_PATH.")


async def load_dynamic_profile(settings: Settings) -> dict[str, Any]:
    global _cached, _cached_path, _cached_mtime_ns
    path = await resolve_profile_path(settings)
    key = str(path)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        mtime_ns = None
    if (
        _cached is not None
        and _cached_path == key
        and _cached_mtime_ns is not None
        and mtime_ns is not None
        and _cached_mtime_ns == mtime_ns
    ):
        return _cached
    raw = path.read_text(encoding="utf-8")
    _cached = json.loads(raw)
    _cached_path = key
    _cached_mtime_ns = mtime_ns
    log.info("Loaded profile from %s", key)
    return _cached


def clear_profile_cache() -> None:
    global _cached, _cached_path, _cached_mtime_ns
    _cached = None
    _cached_path = None
    _cached_mtime_ns = None


def normalize_overview(overview: Any) -> dict[str, str]:
    """API contract: headline + single summary string when JSON uses tiered summaries."""
    if not isinstance(overview, dict):
        return {"headline": "", "summary": ""}
    headline = str(overview.get("headline") or "").strip()
    s = overview.get("summary")
    if isinstance(s, dict):
        body = s.get("medium") or s.get("long") or s.get("short") or ""
        summary = str(body).strip() if body is not None else ""
    else:
        summary = str(s or "").strip()
    return {"headline": headline, "summary": summary}


def normalize_projects_list(raw: Any) -> list[dict[str, Any]]:
    """Flatten ``projects`` from ``dynamic-profile.json`` for the API.

    Accepts a flat list of project dicts, or the legacy nested shape
    ``[{"projects": [{"id", "title", ...}, ...]}]``.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        nested = item.get("projects")
        if isinstance(nested, list):
            for p in nested:
                if isinstance(p, dict):
                    out.append(p)
            continue
        if item.get("title") is not None or item.get("id") is not None:
            out.append(item)
    return out


def normalize_skills(raw: Any) -> list[str]:
    """
    Backward/forward compatible skills normalizer.

    Accepts:
    - legacy: ["TypeScript", "React", ...]
    - current contract: {"languages": [...], "backend": [...], ...}
    Returns: flat de-duplicated list (stable-ish order).
    """
    out: list[str] = []

    def push(v: Any) -> None:
        s = str(v or "").strip()
        if not s:
            return
        out.append(s)

    if isinstance(raw, list):
        for x in raw:
            push(x)
    elif isinstance(raw, dict):
        # Preserve a reasonable priority order for UI/prompt usefulness.
        preferred = [
            "languages",
            "backend",
            "frontend",
            "databases",
            "cloud",
            "devops",
            "ai",
            "other",
        ]
        keys = [*preferred, *[k for k in raw.keys() if k not in preferred]]
        for k in keys:
            xs = raw.get(k)
            if isinstance(xs, list):
                for x in xs:
                    push(x)

    seen: set[str] = set()
    deduped: list[str] = []
    for s in out:
        low = s.lower()
        if low in seen:
            continue
        seen.add(low)
        deduped.append(s)
    return deduped


def _truncate_block(s: str, max_chars: int) -> str:
    t = s.strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 24] + "\n…[truncated]"


def overview_prompt_block(overview: Any, *, max_chars: int = 2500) -> str:
    """Structured blurb for the system prompt (tiers preserved when present)."""
    if not isinstance(overview, dict):
        return ""
    headline = str(overview.get("headline") or "").strip()
    s = overview.get("summary")
    lines: list[str] = []
    if headline:
        lines.append(f"Headline: {headline}")
    if isinstance(s, dict):
        for key in ("short", "medium", "long"):
            v = s.get(key)
            if v is not None and str(v).strip():
                lines.append(f"{key.capitalize()} summary: {str(v).strip()}")
    elif s is not None and str(s).strip():
        lines.append(f"Summary: {str(s).strip()}")
    if not lines:
        return ""
    return _truncate_block("\n".join(lines), max_chars)


def static_contact() -> dict[str, str]:
    """Canonical contact — mirrored in ``apps/frontend/.../ProfileConfig`` for the Contact tab."""
    return {
        "email": "tdjosy@gmail.com",
        "phone": "+251-923-52-22-53",
        "website": "https://jose-dev-six.vercel.app",
        "linkedIn": "https://linkedin.com/in/eyosiyas-tadele",
        "address": "Addis Ababa, Ethiopia",
    }


def canonical_contact_prompt_block() -> str:
    """Facts only — system prompt defines when to emit (explicit contact ask, zero preamble)."""
    c = static_contact()
    lines = [
        f"Email: {c['email']}",
        f"Phone: {c['phone']}",
        f"Website: {c['website']}",
        f"LinkedIn: {c['linkedIn']}",
        "Product (Habesha Network): https://habeshanetwork.com",
    ]
    addr = (c.get("address") or "").strip()
    if addr:
        lines.append(f"- Location: {addr}")
    return "\n".join(lines)


def static_availability() -> dict[str, str]:
    return {
        "availability": "Full-stack systems, event-driven backends, AI-integrated products",
        "availabilityDetail": (
            "I focus on shipping NestJS/Node services, Kafka/Redis pipelines, React/Next UIs, "
            "and production-grade integrations — not job-status wording."
        ),
    }
