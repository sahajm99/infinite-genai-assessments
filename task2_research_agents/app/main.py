"""Task 2 — Multi-Agent Research Assistant (FastAPI + LangGraph)."""
from __future__ import annotations

import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from rag_core import get_settings
from rag_core.llm import LLMClient, LLMError
from rag_core.pipeline import retrieve

from .agents import report_agent, research_agent, summarizer_agent, run_pipeline
from .state import Report

COLLECTION = "research"
settings = get_settings()

app = FastAPI(
    title="Multi-Agent Research Assistant (Task 2)",
    description="Research a topic with three agents and generate a structured report.",
    version="1.0.0",
)


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    mode: str = Field(default="corpus", pattern="^(corpus|web)$")


def get_llm() -> LLMClient:
    try:
        return LLMClient(settings)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _retrieve_fn(query: str):
    try:
        return retrieve(query, COLLECTION, settings.top_k, settings)
    except Exception:  # noqa: BLE001 - research degrades gracefully to no-context
        return []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research", response_model=Report)
def research(req: ResearchRequest, llm=Depends(get_llm)):
    """Run the full graph and return the structured report."""
    try:
        from .graph import run_graph

        state = run_graph(req.topic, llm, _retrieve_fn, req.mode)
    except ImportError:
        # langgraph not installed -> deterministic sequential fallback
        state = run_pipeline(req.topic, llm, _retrieve_fn, req.mode)
    report = state.get("report") or Report()
    return report


@app.post("/research/stream")
def research_stream(req: ResearchRequest, llm=Depends(get_llm)):
    """Stream each agent's progress as Server-Sent Events (bonus)."""

    def events():
        state = {"topic": req.topic, "mode": req.mode, "errors": []}
        state.update(research_agent(state, llm, _retrieve_fn))
        yield _sse("research_done", {"subquestions": state.get("subquestions", []),
                                     "findings": len(state.get("findings", []))})
        state.update(summarizer_agent(state, llm))
        yield _sse("summary_done", {"summary": state.get("summary", "")})
        state.update(report_agent(state, llm))
        report = state.get("report") or Report()
        yield _sse("report_done", report.model_dump())

    return StreamingResponse(events(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
