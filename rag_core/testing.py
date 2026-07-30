"""Fakes so apps and core can be unit-tested without a network or API key."""
from __future__ import annotations

from .schemas import Source


class FakeLLM:
    """Deterministic LLM stand-in. Returns a canned reply or echoes context."""

    def __init__(self, reply: str = "Grounded answer [1].", json_reply: dict | None = None):
        self.reply = reply
        self.json_reply = json_reply or {}
        self.calls: list[list[dict]] = []

    def complete(self, messages, temperature: float = 0.2, **kw) -> str:
        self.calls.append(messages)
        return self.reply

    def complete_json(self, messages, temperature: float = 0.0) -> dict:
        self.calls.append(messages)
        return self.json_reply

    def stream(self, messages, temperature: float = 0.2):
        self.calls.append(messages)
        yield self.reply


class FakeEmbedder:
    """Hash-based deterministic vectors; no model download."""

    def __init__(self, dim: int = 16):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            vec = [0.0] * self.dim
            for i, ch in enumerate(t):
                vec[i % self.dim] += (ord(ch) % 17) / 17.0
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            out.append([v / norm for v in vec])
        return out


def make_sources(*pairs: tuple[str, float]) -> list[Source]:
    """Build Source list from (text, score) tuples for grounding tests."""
    return [
        Source(id=f"s{i}", text=txt, metadata={"source": "test"}, score=score)
        for i, (txt, score) in enumerate(pairs)
    ]
