"""Recursive character chunking that preserves source metadata."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from .loaders import RawDoc

_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


def _split(text: str, size: int, overlap: int) -> list[str]:
    """Greedy split honoring natural boundaries, with overlap."""
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # try to break on the nearest separator before `end`
            window = text[start:end]
            cut = max((window.rfind(sep) for sep in _SEPARATORS), default=-1)
            if cut > size * 0.5:  # only honor a boundary that isn't too early
                end = start + cut + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_documents(
    docs: list[RawDoc], size: int = 800, overlap: int = 120
) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        for piece in _split(doc.text, size, overlap):
            cid = hashlib.sha1(
                f"{doc.metadata.get('source','')}:{doc.metadata.get('page','')}:{piece[:64]}".encode()
            ).hexdigest()[:16]
            out.append(Chunk(cid, piece, dict(doc.metadata)))
    return out
