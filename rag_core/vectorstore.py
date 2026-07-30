"""Persistent Chroma vector store wrapper with cosine similarity."""
from __future__ import annotations

from .chunking import Chunk
from .config import Settings, get_settings
from .schemas import Source


class VectorStore:
    def __init__(self, collection: str = "docs", settings: Settings | None = None):
        import chromadb

        self.settings = settings or get_settings()
        self._client = chromadb.PersistentClient(path=self.settings.chroma_dir)
        self._col = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
        self._col.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[c.metadata or {"source": "unknown"} for c in chunks],
        )
        return len(chunks)

    def search(self, query_embedding: list[float], k: int | None = None) -> list[Source]:
        k = k or self.settings.top_k
        if self.count() == 0:
            return []
        res = self._col.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        sources: list[Source] = []
        ids = res.get("ids", [[]])[0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for id_, doc, meta, dist in zip(ids, docs, metas, dists):
            # cosine distance -> similarity in [0, 1]
            sources.append(
                Source(id=id_, text=doc, metadata=meta or {}, score=round(1.0 - dist, 4))
            )
        return sources

    def count(self) -> int:
        return self._col.count()

    def reset(self) -> None:
        self._client.delete_collection(self._col.name)
        self._col = self._client.get_or_create_collection(
            name=self._col.name, metadata={"hnsw:space": "cosine"}
        )
