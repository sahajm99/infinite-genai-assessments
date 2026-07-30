# Task 1 — RAG Clinical Knowledge Assistant

Answers clinical questions grounded **only** in a provided document corpus. Built on the
shared [`rag_core`](../rag_core) engine.

> ⚠️ The corpus is **synthetic and fictional**, for demonstration only — not medical advice.

## What it does
Load docs → chunk → embed (OpenAI) → store in Chroma → retrieve top-k → answer strictly
from context, with citations, or refuse with *"I don't have enough information…"*.

## Run it

### Option A — Docker (recommended)
```bash
# from the repo root
cp .env.example .env      # add your OPENAI_API_KEY
docker compose up task1
# API at http://localhost:8001/docs
```

### Option B — Local
```bash
# from repo root
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[ui]" && pip install requests
cd task1_clinical_rag
export OPENAI_API_KEY=sk-...       # or put it in ../.env
python -m app.ingest               # build the index
uvicorn app.main:app --port 8001
```

### Streamlit UI (bonus)
```bash
cd task1_clinical_rag
streamlit run streamlit_app.py     # talks to the API on :8001
```

## API

`POST /ask`
```json
{ "question": "What is the first-line agent for stage 1 hypertension?",
  "session_id": "optional-for-memory", "top_k": 4 }
```
Response: `{ answer, sources[], grounded, latency_ms }`.

Other endpoints: `POST /ingest` (rebuild index), `GET /health` (doc count), `GET /docs`.

```bash
curl -X POST localhost:8001/ask -H "Content-Type: application/json" \
  -d '{"question":"Target INR for atrial fibrillation on warfarin?"}'
```

## 5 evaluation questions
1. What is the first-line pharmacologic agent for stage 1 hypertension? *(→ thiazide diuretic)*
2. What is the target INR range for atrial fibrillation on warfarin? *(→ 2.0–3.0)*
3. What is the preferred initial medication for type 2 diabetes? *(→ metformin)*
4. Which vasopressor is first-line in septic shock? *(→ norepinephrine)*
5. What is the capital of France? *(→ refuses: out of corpus scope — proves grounding)*

## How it meets the rubric
| Criterion | Where |
|-----------|-------|
| Working RAG (30%) | `rag_core.pipeline` + Chroma |
| API (20%) | FastAPI `/ask` `/ingest` `/health` + OpenAPI `/docs` |
| Grounding (20%) | `rag_core.grounding` threshold + refusal + citations |
| Code quality (15%) | shared core, typed schemas, DI, tests |
| README (10%) | this file |
| Error handling (5%) | typed errors → structured HTTP; empty-corpus guard |
| Bonus | memory (`session_id`), citations, Docker, Streamlit, `latency_ms` |

## Tests
```bash
cd task1_clinical_rag && python -m pytest -q   # uses fakes, no API key needed
```
