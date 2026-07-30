# Task 3 — AI Customer Support Copilot

Answers from internal FAQ docs, remembers the conversation per session, and **escalates**
low-confidence queries to a human. Built on the shared [`rag_core`](../rag_core) engine —
it is Task 1's RAG + grounding plus durable memory and an escalation decision.

## Run it

### Docker (recommended)
```bash
# from repo root
cp .env.example .env      # add OPENAI_API_KEY
docker compose up task3   # API at http://localhost:8003/docs
```
Redis memory (bonus): `docker compose up task3 redis` and set `MEMORY_BACKEND=redis` in `.env`.

### Local
```bash
pip install -e . && pip install requests streamlit
cd task3_support_copilot
export OPENAI_API_KEY=sk-...
python -m app.ingest
uvicorn app.main:app --port 8003
streamlit run streamlit_app.py    # optional chat UI
```

## API

`POST /chat`
```json
{ "session_id": "user-123", "message": "What are the API rate limits on the Team plan?" }
```
Response: `{ session_id, answer, escalate, confidence, sources[] }`.

Other endpoints: `GET /session/{id}` (history), `POST /ingest`, `GET /health`, `GET /docs`.

```bash
curl -X POST localhost:8003/chat -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"How do I reset my password?"}'
```

## Demo script
1. `"What plans do you offer?"` → grounded answer, `escalate=false`.
2. `"And how much is the Team plan annually?"` → uses **memory** to resolve "the Team plan".
3. `"Do you integrate with SAP?"` → not in FAQ → `escalate=true`, hand-off message.

## How it meets the rubric
| Criterion | Where |
|-----------|-------|
| Memory | `rag_core.memory` (in-memory or Redis) keyed by `session_id` |
| Retrieval quality | `rag_core` Chroma retrieval, scored |
| Hallucination prevention | `rag_core.grounding` context-only + refusal |
| API design | `POST /chat` with session + escalation flag + citations |
| Bonus | Redis memory, source citations, highlighted evidence (UI) |

## Tests
```bash
cd task3_support_copilot && python -m pytest -q
```
