"""Embedding backends: OpenAI (default) or local sentence-transformers."""
from __future__ import annotations

from typing import Protocol

from .config import Settings, get_settings


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    def __init__(self, settings: Settings | None = None):
        from openai import OpenAI

        self.settings = settings or get_settings()
        kwargs = {"api_key": self.settings.openai_api_key}
        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url
        self.client = OpenAI(**kwargs)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self.client.embeddings.create(
            model=self.settings.embed_model, input=texts
        )
        return [d.embedding for d in resp.data]


class LocalEmbedder:
    """Offline fallback — no API key required."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self.model.encode(texts, normalize_embeddings=True).tolist()


def get_embedder(settings: Settings | None = None) -> Embedder:
    settings = settings or get_settings()
    if settings.embed_backend == "local":
        return LocalEmbedder()
    return OpenAIEmbedder(settings)
