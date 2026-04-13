"""
Ingestion chunking — mirrored from legacy ``chunk.ts`` (do not change algorithm).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

MAX_CHARS = 1200
OVERLAP = 120

ChunkSource = Literal["cv", "linkedin", "website", "summary"]
ChunkType = Literal["project", "skill", "experience", "summary"]


class RagChunkPayload(TypedDict):
    type: ChunkType
    source: ChunkSource
    text: str
    title: NotRequired[str | None]


@dataclass(frozen=True)
class WebsitePage:
    url: str
    title: str | None
    text: str


def split_into_overlapping_chunks(text: str) -> list[str]:
    t = text.replace("\r\n", "\n").strip()
    if len(t) <= MAX_CHARS:
        return [t] if t else []

    parts: list[str] = []
    start = 0
    while start < len(t):
        end = min(start + MAX_CHARS, len(t))
        slice_ = t[start:end]
        if end < len(t):
            last_break = max(slice_.rfind("\n\n"), slice_.rfind(". "))
            if last_break > MAX_CHARS * 0.4:
                slice_ = slice_[: last_break + 1].strip()
        if slice_:
            parts.append(slice_)
        step = max(1, len(slice_) - OVERLAP)
        start += step
    return parts


def infer_type_from_line(line: str) -> ChunkType | None:
    u = line.upper()
    if re.search(r"PROJECT|PORTFOLIO|SELECTED WORK|OPEN SOURCE", u) and len(u) < 80:
        return "project"
    if re.search(r"SKILL|TECHNOLOG|STACK|TOOLS|COMPETENC", u) and len(u) < 80:
        return "skill"
    if re.search(r"EXPERIENCE|EMPLOYMENT|WORK HISTORY|PROFESSIONAL|CAREER", u) and len(u) < 80:
        return "experience"
    if re.search(r"SUMMARY|PROFILE|ABOUT|OBJECTIVE", u) and len(u) < 80:
        return "summary"
    return None


def chunk_plain_text(raw: str, source: ChunkSource, default_type: ChunkType) -> list[RagChunkPayload]:
    lines = raw.replace("\r\n", "\n").split("\n")

    class Block:
        __slots__ = ("type", "heading", "lines")

        def __init__(self, typ: ChunkType, heading: str | None = None) -> None:
            self.type = typ
            self.heading = heading
            self.lines: list[str] = []

    cur = Block(default_type)
    blocks: list[Block] = []

    def push_cur() -> None:
        text = "\n".join(cur.lines).strip()
        if text:
            blocks.append(cur)

    for line in lines:
        t = line.strip()
        inferred = infer_type_from_line(t) if t else None
        if inferred and len(t) < 100:
            push_cur()
            cur = Block(inferred, t)
            continue
        cur.lines.append(line)
    push_cur()

    if not blocks:
        return [
            {"type": default_type, "source": source, "text": c}
            for c in split_into_overlapping_chunks(raw)
        ]

    out: list[RagChunkPayload] = []
    for sec in blocks:
        chunks = split_into_overlapping_chunks("\n".join(sec.lines))
        for text in chunks:
            row: RagChunkPayload = {"type": sec.type, "source": source, "text": text}
            if sec.heading:
                row["title"] = sec.heading
            out.append(row)
    return out


def chunk_website_pages(pages: list[WebsitePage]) -> list[RagChunkPayload]:
    out: list[RagChunkPayload] = []
    for p in pages:
        header = f"{p.title or p.url}\n"
        chunks = split_into_overlapping_chunks(header + p.text)
        for text in chunks:
            out.append(
                {
                    "type": "project",
                    "source": "website",
                    "text": text,
                    "title": p.title or p.url,
                }
            )
    return out
