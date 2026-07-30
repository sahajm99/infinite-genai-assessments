"""High-level ingest + retrieve helpers composed from the core modules."""
from __future__ import annotations

from .chunking import chunk_documents
from .config import Settings, get_settings
from .embeddings import get_embedder
from .loaders import load_documents
from .schemas import Source
from .vectorstore import VectorStore


def build_index(
    data_dir: str, collection: str = "docs", settings: Settings | None = None
) -> int:
    """Load -> chunk -> embed -> upsert. Returns number of chunks indexed."""
    settings = settings or get_settings()
    docs = load_documents(data_dir)
    chunks = chunk_documents(docs, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        return 0
    embedder = get_embedder(settings)
    vectors = embedder.embed([c.text for c in chunks])
    store = VectorStore(collection, settings)
    return store.add(chunks, vectors)


def retrieve(
    query: str,
    collection: str = "docs",
    k: int | None = None,
    settings: Settings | None = None,
) -> list[Source]:
    settings = settings or get_settings()
    embedder = get_embedder(settings)
    store = VectorStore(collection, settings)
    query_vec = embedder.embed([query])[0]
    return store.search(query_vec, k or settings.top_k)
