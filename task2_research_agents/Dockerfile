# Build context = repo root (see docker-compose.yml)
FROM python:3.11-slim
WORKDIR /srv

COPY pyproject.toml ./
COPY rag_core ./rag_core
RUN pip install --no-cache-dir ".[agents]"

COPY task2_research_agents ./task2_research_agents
WORKDIR /srv/task2_research_agents

EXPOSE 8002
# Ingest seed corpus (idempotent) then serve.
CMD ["sh", "-c", "python -m app.ingest || true; uvicorn app.main:app --host 0.0.0.0 --port 8002"]
