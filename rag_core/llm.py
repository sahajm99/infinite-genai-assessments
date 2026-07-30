"""OpenAI chat wrapper: completion, JSON mode, streaming."""
from __future__ import annotations

import json
from typing import Iterator

from .config import Settings, get_settings


class LLMError(RuntimeError):
    """Raised when the LLM call fails irrecoverably."""


class LLMClient:
    def __init__(self, settings: Settings | None = None):
        from openai import OpenAI

        self.settings = settings or get_settings()
        if not self.settings.has_key:
            raise LLMError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def complete(self, messages: list[dict], temperature: float = 0.2, **kw) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=temperature,
                **kw,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            raise LLMError(str(exc)) from exc

    def complete_json(self, messages: list[dict], temperature: float = 0.0) -> dict:
        """Force a JSON object response. Prompt must describe the schema."""
        try:
            resp = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content or "{}")
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model did not return valid JSON: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMError(str(exc)) from exc

    def stream(self, messages: list[dict], temperature: float = 0.2) -> Iterator[str]:
        try:
            stream = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:  # noqa: BLE001
            raise LLMError(str(exc)) from exc
