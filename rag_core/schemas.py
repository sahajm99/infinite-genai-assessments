"""Pydantic models shared across apps."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    text: str
    metadata: dict = Field(default_factory=dict)
    score: float = 0.0


class Answer(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    grounded: bool = True
    latency_ms: float = 0.0


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str
