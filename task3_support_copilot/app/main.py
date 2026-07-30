"""Task 3 — AI Customer Support Copilot (FastAPI).

RAG over an internal FAQ corpus + per-session memory + low-confidence escalation.
Reuses rag_core wholesale; adds only the escalation decision and durable memory.
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_core import ChatTurn, answer_from_context, get_settings
from rag_core.llm import LLMClient, LLMError
from rag_core.memory import get_store
from rag_core.pipeline import build_index, retrieve
from rag_core.schemas import Source

COLLECTION = "faq"
settings = get_settings()
store = get_store(settings)

ESCALATION_MSG = (
    "I'm not fully confident I can answer that accurately, so I'm routing you to a "
    "human support agent who can help further."
)

app = FastAPI(
    title="Customer Support Copilot (Task 3)",
    description="Answers from internal FAQ docs, remembers the conversation, escalates low-confidence queries.",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    escalate: bool
    confidence: float
    sources: list[Source] = []


def get_llm() -> LLMClient:
    try:
        return LLMClient(settings)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def get_retriever():
    return lambda q, k: retrieve(q, COLLECTION, k, settings)


@app.get("/health")
def health():
    try:
        from rag_core.vectorstore import VectorStore

        count = VectorStore(COLLECTION, settings).count()
    except Exception:  # noqa: BLE001
        count = -1
    return {"status": "ok", "doc_count": count, "memory_backend": settings.memory_backend}


@app.post("/ingest")
def ingest():
    try:
        n = build_index("data", COLLECTION, settings)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"chunks_indexed": n}


@app.get("/session/{session_id}")
def session_history(session_id: str):
    turns = store.history(session_id, n=50)
    return {"session_id": session_id, "turns": [t.model_dump() for t in turns]}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, llm=Depends(get_llm), retriever=Depends(get_retriever)):
    try:
        sources = retriever(req.message, settings.top_k)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    confidence = max((s.score for s in sources), default=0.0)
    history = store.history(req.session_id, settings.memory_window)
    result = answer_from_context(
        req.message, sources, llm, settings.score_threshold, history
    )

    escalate = (not result.grounded) or confidence < settings.escalate_threshold
    answer_text = ESCALATION_MSG if escalate else result.answer

    # Always log the turn (including escalations) so context carries forward.
    store.append(req.session_id, ChatTurn(role="user", content=req.message))
    store.append(req.session_id, ChatTurn(role="assistant", content=answer_text))

    return ChatResponse(
        session_id=req.session_id,
        answer=answer_text,
        escalate=escalate,
        confidence=round(confidence, 4),
        sources=sources,
    )
