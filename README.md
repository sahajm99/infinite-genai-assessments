# Infinite — GenAI Engineer Assessments

Four GenAI prototype services, built on **one shared engine** (`rag_core`) rather than four
copies of the same machinery. Each task is independently runnable and reviewable, and every
app maps its design decisions to the assessment rubric.

| # | Task | Endpoint | Port | Docs |
|---|------|----------|------|------|
| 1 | RAG Clinical Knowledge Assistant | `POST /ask` | 8001 | [design](docs/01_task1_clinical_rag.md) · [readme](task1_clinical_rag/README.md) |
| 2 | Multi-Agent Research Assistant | `POST /research` | 8002 | [design](docs/02_task2_research_agents.md) · [readme](task2_research_agents/README.md) |
| 3 | AI Customer Support Copilot | `POST /chat` | 8003 | [design](docs/03_task3_support_copilot.md) · [readme](task3_support_copilot/README.md) |
| 4 | AI Resume Screening & Ranking | `POST /rank` | 8004 | [design](docs/04_task4_resume_ranker.md) · [readme](task4_resume_ranker/README.md) |

Architecture overview: [docs/00_ARCHITECTURE.md](docs/00_ARCHITECTURE.md).

## The idea

Tasks 1–4 share ~70% of their logic: load → chunk → embed → store → retrieve → **ground** →
**remember**. That lives once in [`rag_core/`](rag_core). The four apps are thin FastAPI
layers that compose it:

```
rag_core (config · loaders · chunking · embeddings · vectorstore · llm · grounding · memory)
   │
   ├── task1_clinical_rag     RAG + citations + latency
   ├── task2_research_agents  3-agent LangGraph pipeline
   ├── task3_support_copilot  RAG + session memory + escalation
   └── task4_resume_ranker    parse + extract + hybrid score + rank
```

## Quick start

```bash
cp .env.example .env          # add your OPENAI_API_KEY
docker compose up             # builds + runs all four (+ redis)
# then open the interactive API docs:
#   http://localhost:8001/docs   (clinical RAG)
#   http://localhost:8002/docs   (research agents)
#   http://localhost:8003/docs   (support copilot)
#   http://localhost:8004/docs   (resume ranker)
```

Run a single task: `docker compose up task1` (or task2 / task3 / task4).

## Using Groq (open-source models) instead of OpenAI

Every LLM call goes through one OpenAI-compatible client, so you can point it at **Groq**
with no code changes. Groq has **no embeddings API**, so pair it with local HuggingFace
embeddings (already built in via `EMBED_BACKEND=local`). In your `.env`:

```bash
OPENAI_API_KEY=gsk_your_groq_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile     # or llama-3.1-8b-instant, openai/gpt-oss-20b
EMBED_BACKEND=local                    # embeddings run offline (sentence-transformers)
```

Then `docker compose up` as usual. First run downloads a ~90 MB embedding model; the Docker
images include `sentence-transformers` so nothing else is needed. Generation is served by
Groq; retrieval/scoring embeddings are computed locally.

## Local dev (no Docker)

```bash
python -m venv .venv && source .venv/Scripts/activate    # Windows: .venv\Scripts\activate
pip install -e ".[agents,ui,redis,dev]"
export OPENAI_API_KEY=sk-...
# each app: cd taskN_... ; python -m app.ingest (if it has data) ; uvicorn app.main:app --port 800N
```

## Tests (no API key needed — everything uses injectable fakes)

```bash
pip install -e ".[dev]" && pip install fastapi "httpx<0.28"
pytest tests task1_clinical_rag/tests task3_support_copilot/tests \
       task4_resume_ranker/tests task2_research_agents/tests -q
```

## Design highlights a reviewer will notice

- **Grounding is a first-class module** (`rag_core/grounding.py`): refuses *before* spending
  a token when retrieval is weak, and verifies the model stayed on-context. Shared by the
  two tasks graded on hallucination prevention.
- **Dependency-injected LLM/embedder/retriever** → every app is unit-tested offline.
- **Graceful degradation everywhere**: one bad document, sub-question, or resume never
  takes down a request; Redis falls back to in-memory; missing key → clean 503.
- **Docker-first** so `git clone && docker compose up` reproduces the whole suite.

> All sample corpora (clinical notes, FAQ, resumes, research seed) are **synthetic and
> fictional**, included so every demo runs with zero external data.
