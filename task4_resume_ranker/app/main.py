"""Task 4 — AI Resume Screening & Candidate Ranking (FastAPI)."""
from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from rag_core import get_settings
from rag_core.embeddings import get_embedder
from rag_core.llm import LLMClient, LLMError

from .extractor import extract_profile
from .models import RankRequest, RankResponse, RankedCandidate, SkippedResume
from .parser import clean_text, parse_upload
from .scorer import score_candidate

settings = get_settings()

app = FastAPI(
    title="Resume Screening & Ranking (Task 4)",
    description="Rank resumes against a job description with strengths, gaps, and hybrid scores.",
    version="1.0.0",
)


def get_llm() -> LLMClient:
    try:
        return LLMClient(settings)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def get_embedder_dep():
    return get_embedder(settings)


@app.get("/health")
def health():
    return {"status": "ok", "llm_model": settings.llm_model}


def _rank(jd: str, resumes: list[tuple[str, str]], llm, embedder) -> RankResponse:
    """Core ranking over (id, text) pairs. One bad resume never sinks the batch."""
    ranked: list[RankedCandidate] = []
    skipped: list[SkippedResume] = []
    for cid, text in resumes:
        text = clean_text(text)
        if len(text) < 30:
            skipped.append(SkippedResume(id=cid, reason="empty or unparseable resume"))
            continue
        try:
            profile = extract_profile(text, llm)
            ranked.append(score_candidate(cid, profile, text, jd, llm, embedder))
        except Exception as exc:  # noqa: BLE001 - isolate per-candidate failure
            skipped.append(SkippedResume(id=cid, reason=f"scoring failed: {exc}"))
    ranked.sort(key=lambda c: c.score, reverse=True)
    return RankResponse(
        job_description_summary=jd[:200] + ("..." if len(jd) > 200 else ""),
        ranked=ranked,
        skipped=skipped,
    )


@app.post("/rank", response_model=RankResponse)
def rank(req: RankRequest, llm=Depends(get_llm), embedder=Depends(get_embedder_dep)):
    pairs = [(r.id, r.text) for r in req.resumes]
    return _rank(req.job_description, pairs, llm, embedder)


@app.post("/rank/upload", response_model=RankResponse)
async def rank_upload(
    job_description: str = Form(...),
    files: list[UploadFile] = File(...),
    llm=Depends(get_llm),
    embedder=Depends(get_embedder_dep),
):
    pairs: list[tuple[str, str]] = []
    for f in files:
        data = await f.read()
        pairs.append((f.filename, parse_upload(f.filename, data)))
    return _rank(job_description, pairs, llm, embedder)
