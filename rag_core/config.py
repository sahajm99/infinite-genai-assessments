"""Typed, env-driven configuration shared by all four apps."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- OpenAI ---
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"

    # --- backends ---
    embed_backend: str = "openai"          # "openai" | "local"
    memory_backend: str = "memory"         # "memory" | "redis"
    redis_url: str = "redis://localhost:6379/0"

    # --- retrieval / chunking ---
    chroma_dir: str = "./.chroma"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4
    score_threshold: float = 0.35          # below this -> "insufficient info"
    escalate_threshold: float = 0.30       # Task 3 escalation
    memory_window: int = 6

    @property
    def has_key(self) -> bool:
        return bool(self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
