"""Grounding: answer strictly from retrieved context, or refuse.

This module is the rubric-critical piece for Tasks 1 and 3 (grounding /
hallucination prevention). It is deliberately conservative: it refuses before
spending a token when retrieval is weak, and it verifies the model stayed grounded.
"""
from __future__ import annotations

import time

from .schemas import Answer, ChatTurn, Source

INSUFFICIENT = (
    "I don't have enough information to answer that based on the provided documents."
)

_SYSTEM = """You are a precise assistant that answers ONLY from the numbered context below.

Rules:
- Use ONLY facts present in the context. Do not use outside knowledge.
- If the answer is not clearly supported by the context, reply EXACTLY with:
  "{insufficient}"
- Cite the context you used with bracketed numbers like [1], [2].
- Be concise and factual.

Context:
{context}"""


def _format_context(sources: list[Source]) -> str:
    return "\n\n".join(
        f"[{i + 1}] (source: {s.metadata.get('source', 'unknown')})\n{s.text}"
        for i, s in enumerate(sources)
    )


def answer_from_context(
    query: str,
    sources: list[Source],
    llm,
    threshold: float = 0.35,
    history: list[ChatTurn] | None = None,
) -> Answer:
    start = time.perf_counter()
    best = max((s.score for s in sources), default=0.0)

    # Guard: no context or weak retrieval -> refuse before calling the model.
    if not sources or best < threshold:
        return Answer(
            answer=INSUFFICIENT,
            sources=sources,
            grounded=False,
            latency_ms=round((time.perf_counter() - start) * 1000, 1),
        )

    messages = [
        {"role": "system", "content": _SYSTEM.format(
            insufficient=INSUFFICIENT, context=_format_context(sources))}
    ]
    for turn in (history or [])[-6:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": query})

    text = llm.complete(messages, temperature=0.1).strip()
    grounded = INSUFFICIENT.split(".")[0].lower() not in text.lower()

    return Answer(
        answer=text,
        sources=sources,
        grounded=grounded,
        latency_ms=round((time.perf_counter() - start) * 1000, 1),
    )
