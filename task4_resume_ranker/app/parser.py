"""Resume parsing: bytes/text/PDF -> clean text."""
from __future__ import annotations

import io


def parse_pdf_bytes(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def parse_upload(filename: str, data: bytes) -> str:
    """Return clean text from an uploaded resume file."""
    if filename.lower().endswith(".pdf"):
        return parse_pdf_bytes(data)
    return data.decode("utf-8", errors="ignore").strip()


def clean_text(text: str) -> str:
    return " ".join(text.split())
