# Build context = repo root (see docker-compose.yml)
FROM python:3.11-slim
WORKDIR /srv

COPY pyproject.toml ./
COPY rag_core ./rag_core
RUN pip install --no-cache-dir ".[local-embed,redis]" requests streamlit

COPY task3_support_copilot ./task3_support_copilot
WORKDIR /srv/task3_support_copilot

EXPOSE 8003
CMD ["sh", "-c", "python -m app.ingest && uvicorn app.main:app --host 0.0.0.0 --port 8003"]
