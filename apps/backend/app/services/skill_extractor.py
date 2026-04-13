"""Merge skills from dynamic-profile.json with light hints from CV/LinkedIn text."""

from __future__ import annotations

import re

from app.core.config import Settings
from app.services import profile_store


def _unique_preserve(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        t = x.strip()
        if len(t) < 2 or t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append(t)
    return out


async def load_skills_from_profile(settings: Settings) -> list[str]:
    try:
        prof = await profile_store.load_dynamic_profile(settings)
    except Exception:
        return []
    raw = prof.get("skills")
    if not isinstance(raw, list):
        return []
    return [str(x).strip() for x in raw if str(x).strip()]


_TECH = re.compile(
    r"\b("
    r"TypeScript|JavaScript|Python|Rust|Go|Java|Kotlin|C\+\+|Ruby|PHP|Swift|"
    r"React|Next\.js|Vue|Svelte|Angular|Node\.js|Deno|Bun|"
    r"PostgreSQL|MySQL|MongoDB|Redis|DynamoDB|SQL|"
    r"AWS|GCP|Azure|Docker|Kubernetes|Terraform|Lambda|"
    r"FastAPI|Django|Flask|Express|Hono|GraphQL|REST|gRPC"
    r")\b",
    re.I,
)


def _skills_from_free_text(blob: str, cap: int = 24) -> list[str]:
    found = sorted({m.group(1) for m in _TECH.finditer(blob)})[:cap]
    return found


async def extract_skills(
    settings: Settings,
    *,
    cv_text: str,
    linkedin_text: str,
) -> list[str]:
    profile_skills = await load_skills_from_profile(settings)
    hinted = _skills_from_free_text(f"{cv_text}\n{linkedin_text}")
    return _unique_preserve([*profile_skills, *hinted])
