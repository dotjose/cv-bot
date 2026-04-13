from dataclasses import dataclass
from typing import Literal

ChunkType = Literal["project", "skill", "experience", "summary"]
ChunkSource = Literal["cv", "linkedin", "website", "summary"]


@dataclass
class RetrievedContext:
    id: str
    score: float
    type: ChunkType
    source: ChunkSource
    text: str
    title: str | None = None
