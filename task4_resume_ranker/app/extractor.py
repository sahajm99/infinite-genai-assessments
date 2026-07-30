"""LLM extraction of a structured CandidateProfile from resume text."""
from __future__ import annotations

from .models import CandidateProfile
from .prompts import EXTRACT_SYSTEM, extract_user


def extract_profile(resume_text: str, llm) -> CandidateProfile:
    data = llm.complete_json(
        [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": extract_user(resume_text)},
        ]
    )
    # Pydantic coerces/validates; unknown keys ignored, missing use defaults.
    return CandidateProfile.model_validate(data)
