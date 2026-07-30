"""Load PDF / txt / md documents from a directory."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class RawDoc:
    text: str
    metadata: dict = field(default_factory=dict)


def _read_pdf(path: Path) -> list[RawDoc]:
    from pypdf import PdfReader

    docs: list[RawDoc] = []
    reader = PdfReader(str(path))
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            docs.append(RawDoc(text, {"source": path.name, "page": i + 1}))
    return docs


def _read_text(path: Path) -> list[RawDoc]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    return [RawDoc(text, {"source": path.name, "page": 1})] if text else []


def load_documents(path: str | Path) -> list[RawDoc]:
    """Walk a directory (or single file) and return readable documents.

    Unreadable files are logged and skipped rather than crashing ingestion.
    """
    root = Path(path)
    paths = [root] if root.is_file() else sorted(root.rglob("*"))
    docs: list[RawDoc] = []
    for p in paths:
        if not p.is_file():
            continue
        try:
            if p.suffix.lower() == ".pdf":
                docs.extend(_read_pdf(p))
            elif p.suffix.lower() in {".txt", ".md"}:
                docs.extend(_read_text(p))
        except Exception as exc:  # noqa: BLE001 - skip bad file, keep ingesting
            log.warning("Skipping unreadable file %s: %s", p, exc)
    return docs
