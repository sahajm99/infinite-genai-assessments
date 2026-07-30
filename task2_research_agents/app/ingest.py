"""CLI: python -m app.ingest — build the research seed corpus (for 'corpus' mode)."""
from rag_core import get_settings
from rag_core.pipeline import build_index

if __name__ == "__main__":
    n = build_index("data", "research", get_settings())
    print(f"Indexed {n} chunks into the 'research' collection.")
