# Task 2 — Multi-Agent Research Assistant

Three cooperating agents research a topic and produce a structured report. Orchestrated as
a **LangGraph** state machine: `Research → Summarize → Report`.

```
topic ─▶ [Research Agent] ─▶ [Summarizer Agent] ─▶ [Report Generator] ─▶ structured report
```

- **Research Agent** — decomposes the topic into 3–5 sub-questions and gathers a grounded
  finding per question. Default `corpus` mode retrieves from a small seed corpus via
  `rag_core` (fully offline/demoable). `web` mode is a stub that degrades to `corpus`.
- **Summarizer Agent** — condenses findings into a narrative.
- **Report Generator** — emits `executive_summary`, `key_findings`, `risks`,
  `recommendations` as schema-locked JSON.

Each agent is a pure `(state) -> state` function; orchestration lives only in `graph.py`.
No agent calls another directly.

## Run it

### Docker (recommended)
```bash
# from repo root
cp .env.example .env      # add OPENAI_API_KEY
docker compose up task2   # API at http://localhost:8002/docs
```

### Local
```bash
pip install -e ".[agents]"
cd task2_research_agents
export OPENAI_API_KEY=sk-...
python -m app.ingest          # seed corpus for 'corpus' mode
uvicorn app.main:app --port 8002
```

## API

`POST /research`
```json
{ "topic": "LLM agents in production", "mode": "corpus" }
```
Response: `{ executive_summary, key_findings[], risks[], recommendations[] }`.

`POST /research/stream` (bonus) — Server-Sent Events: `research_done`, `summary_done`,
`report_done`.

```bash
curl -N -X POST localhost:8002/research/stream -H "Content-Type: application/json" \
  -d '{"topic":"LLM agents in production"}'
```

## How it meets the rubric
| Criterion | Where |
|-----------|-------|
| Agent orchestration | LangGraph graph in `graph.py` (sequential fallback in `agents.py`) |
| Prompts | one focused prompt per agent in `prompts.py` |
| Modular architecture | pure agent functions + typed `ResearchState` |
| Error handling | per-node try/except → errors captured in state, report still generated |
| Clean code | no cross-agent coupling; graph is the only orchestrator |
| Bonus | LangGraph, streaming (`/research/stream`), graceful degradation |

## Tests
```bash
cd task2_research_agents && python -m pytest -q
```
