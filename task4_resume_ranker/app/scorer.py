"""Hybrid scoring: semantic similarity + LLM rubric judgment."""
from __future__ import annotations

import math

from .models import CandidateProfile, RankedCandidate
from .prompts import SCORE_SYSTEM, score_user

SEMANTIC_WEIGHT = 0.4
RUBRIC_WEIGHT = 0.6


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def semantic_score(resume_text: str, jd: str, embedder) -> float:
    vecs = embedder.embed([resume_text, jd])
    # cosine in [-1,1] -> clamp to [0,1]
    return round(max(0.0, _cosine(vecs[0], vecs[1])), 4)


def score_candidate(
    cid: str,
    profile: CandidateProfile,
    resume_text: str,
    jd: str,
    llm,
    embedder,
) -> RankedCandidate:
    sem = semantic_score(resume_text, jd, embedder)
    judged = llm.complete_json(
        [
            {"role": "system", "content": SCORE_SYSTEM},
            {"role": "user", "content": score_user(jd, profile.model_dump(), resume_text)},
        ]
    )
    rubric = float(judged.get("rubric_score", 0))
    combined = round(SEMANTIC_WEIGHT * sem * 100 + RUBRIC_WEIGHT * rubric, 1)
    return RankedCandidate(
        id=cid,
        name=profile.name or cid,
        score=combined,
        semantic_score=sem,
        rubric_score=round(rubric, 1),
        strengths=judged.get("strengths", []),
        gaps=judged.get("gaps", []),
        justification=judged.get("justification", ""),
        profile=profile,
    )
