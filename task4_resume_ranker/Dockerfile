# Build context = repo root (see docker-compose.yml)
FROM python:3.11-slim
WORKDIR /srv

COPY pyproject.toml ./
COPY rag_core ./rag_core
RUN pip install --no-cache-dir ".[local-embed]"

COPY task4_resume_ranker ./task4_resume_ranker
WORKDIR /srv/task4_resume_ranker

EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
