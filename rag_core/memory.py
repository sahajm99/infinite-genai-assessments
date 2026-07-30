"""Conversation memory: in-process dict (default) or Redis (Task 3 bonus)."""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Protocol

from .config import Settings, get_settings
from .schemas import ChatTurn

log = logging.getLogger(__name__)


class ConversationStore(Protocol):
    def append(self, session_id: str, turn: ChatTurn) -> None: ...
    def history(self, session_id: str, n: int = 6) -> list[ChatTurn]: ...


class InMemoryStore:
    def __init__(self):
        self._data: dict[str, list[ChatTurn]] = defaultdict(list)

    def append(self, session_id: str, turn: ChatTurn) -> None:
        self._data[session_id].append(turn)

    def history(self, session_id: str, n: int = 6) -> list[ChatTurn]:
        return self._data.get(session_id, [])[-n:]


class RedisStore:
    def __init__(self, url: str, ttl_seconds: int = 3600):
        import redis  # imported lazily

        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.ttl = ttl_seconds
        self.client.ping()

    def _key(self, session_id: str) -> str:
        return f"chat:{session_id}"

    def append(self, session_id: str, turn: ChatTurn) -> None:
        key = self._key(session_id)
        self.client.rpush(key, json.dumps({"role": turn.role, "content": turn.content}))
        self.client.expire(key, self.ttl)

    def history(self, session_id: str, n: int = 6) -> list[ChatTurn]:
        raw = self.client.lrange(self._key(session_id), -n, -1)
        return [ChatTurn(**json.loads(r)) for r in raw]


def get_store(settings: Settings | None = None) -> ConversationStore:
    settings = settings or get_settings()
    if settings.memory_backend == "redis":
        try:
            return RedisStore(settings.redis_url)
        except Exception as exc:  # noqa: BLE001 - never fail a request over memory
            log.warning("Redis unavailable (%s); falling back to in-memory store.", exc)
    return InMemoryStore()
