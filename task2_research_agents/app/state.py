"""Shared state and output models for the research agent graph."""
from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field


class Finding(BaseModel):
    question: str
    content: str
    sources: list[str] = Field(default_factory=list)


class Report(BaseModel):
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ResearchState(TypedDict, total=False):
    topic: str
    mode: str                    # "corpus" | "web"
    subquestions: list[str]
    findings: list[Finding]
    summary: str
    report: Report
    errors: list[str]
