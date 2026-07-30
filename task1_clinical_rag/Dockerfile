# Build context = repo root (see docker-compose.yml)
FROM python:3.11-slim
WORKDIR /srv

COPY pyproject.toml ./
COPY rag_core ./rag_core
RUN pip install --no-cache-dir . requests streamlit

COPY task1_clinical_rag ./task1_clinical_rag
WORKDIR /srv/task1_clinical_rag

EXPOSE 8001
# Ingest at startup (idempotent) then serve.
CMD ["sh", "-c", "python -m app.ingest && uvicorn app.main:app --host 0.0.0.0 --port 8001"]
