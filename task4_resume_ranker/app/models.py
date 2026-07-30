"""Typed request/response models for the resume ranker."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeInput(BaseModel):
    id: str
    text: str


class RankRequest(BaseModel):
    job_description: str = Field(..., min_length=1)
    resumes: list[ResumeInput] = Field(..., min_length=1)


class Experience(BaseModel):
    title: str = ""
    org: str = ""
    years: float = 0.0


class CandidateProfile(BaseModel):
    name: str = ""
    skills: list[str] = []
    education: list[str] = []
    experience: list[Experience] = []
    certifications: list[str] = []
    total_years: float = 0.0


class RankedCandidate(BaseModel):
    id: str
    name: str
    score: float
    semantic_score: float
    rubric_score: float
    strengths: list[str] = []
    gaps: list[str] = []
    justification: str = ""
    profile: CandidateProfile | None = None


class SkippedResume(BaseModel):
    id: str
    reason: str


class RankResponse(BaseModel):
    job_description_summary: str
    ranked: list[RankedCandidate]
    skipped: list[SkippedResume] = []
