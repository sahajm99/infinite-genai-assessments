"""Task 1 — RAG Clinical Knowledge Assistant (FastAPI)."""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_core import ChatTurn, answer_from_context, get_settings
from rag_core.llm import LLMClient, LLMError
from rag_core.memory import get_store
from rag_core.pipeline import build_index, retrieve
from rag_core.schemas import Answer

COLLECTION = "clinical"
settings = get_settings()
store = get_store(settings)

app = FastAPI(
    title="Clinical Knowledge Assistant (Task 1)",
    description="Ask questions grounded ONLY in a medical document corpus.",
    version="1.0.0",
)


# --- request / response models ---
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)


# --- injectable dependencies (overridden in tests) ---
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
    return {"status": "ok", "doc_count": count}


@app.post("/ingest")
def ingest():
    """(Re)build the index from ./data. Idempotent."""
    try:
        n = build_index("data", COLLECTION, settings)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"chunks_indexed": n}


@app.post("/ask", response_model=Answer)
def ask(req: AskRequest, llm=Depends(get_llm), retriever=Depends(get_retriever)):
    try:
        sources = retriever(req.question, req.top_k)
    except LLMError as exc:  # embedding failure
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    history = store.history(req.session_id) if req.session_id else None
    answer = answer_from_context(
        req.question, sources, llm, settings.score_threshold, history
    )

    if req.session_id:
        store.append(req.session_id, ChatTurn(role="user", content=req.question))
        store.append(req.session_id, ChatTurn(role="assistant", content=answer.answer))
    return answer
