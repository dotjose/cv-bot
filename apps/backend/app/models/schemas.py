"""Pydantic models — must stay aligned with the Next.js client ``ChatRequest`` / ``ApiChatMessage``."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequestBody(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class StoredChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str


class ChatSessionEnvelope(BaseModel):
    session_id: str
    created_at: str
    messages: list[StoredChatMessage]


class ChatSessionSummary(BaseModel):
    session_id: str
    updated_at: str


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionSummary]


class ChatSessionCreateResponse(BaseModel):
    session_id: str
