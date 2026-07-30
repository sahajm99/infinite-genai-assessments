"""CLI: python -m app.ingest  — build the clinical vector index from ./data."""
from rag_core import get_settings
from rag_core.pipeline import build_index

if __name__ == "__main__":
    n = build_index("data", "clinical", get_settings())
    print(f"Indexed {n} chunks into the 'clinical' collection.")
