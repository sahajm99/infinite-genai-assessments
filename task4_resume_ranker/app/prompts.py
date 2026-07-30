"""Prompts for extraction and scoring. Kept together and versioned."""

# Extraction: force a strict JSON profile out of raw resume text.
EXTRACT_SYSTEM = """You extract structured data from a resume. Return ONLY a JSON object
with exactly these keys:
{
  "name": string,
  "skills": [string],
  "education": [string],
  "experience": [{"title": string, "org": string, "years": number}],
  "certifications": [string],
  "total_years": number
}
Infer total_years from the experience. If a field is unknown, use an empty list, "" or 0.
Do not invent facts that are not in the resume."""

# Scoring: judge fit against the job description with a rubric and rationale.
SCORE_SYSTEM = """You are a hiring assistant scoring a candidate against a job description.
Consider required-skill coverage, seniority/experience match, and domain relevance.
Return ONLY a JSON object with exactly these keys:
{
  "rubric_score": number,        // 0-100 overall fit
  "strengths": [string],         // concrete ways the candidate matches the JD
  "gaps": [string],              // JD requirements the candidate is missing
  "justification": string        // one or two sentences
}
Base every point strictly on the provided resume and job description."""


def extract_user(resume_text: str) -> str:
    return f"RESUME:\n{resume_text[:6000]}"


def score_user(jd: str, profile: dict, resume_text: str) -> str:
    return (
        f"JOB DESCRIPTION:\n{jd[:3000]}\n\n"
        f"CANDIDATE PROFILE (extracted):\n{profile}\n\n"
        f"RESUME TEXT (excerpt):\n{resume_text[:3000]}"
    )
