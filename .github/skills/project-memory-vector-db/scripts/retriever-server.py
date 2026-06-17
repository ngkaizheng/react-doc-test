"""
Persistent retrieval server for Project Memory Vector DB system.

Keeps the embedding model loaded in memory so queries are ~50ms instead of ~1s.
Designed for local use only (binds to 127.0.0.1).

Usage:
    pip install fastapi uvicorn
    python retriever-server.py --port 8000

Endpoints:
    GET /search?q=...&k=5&threshold=0.3  → JSON results
    GET /health                           → {"status": "ok"}
    GET /stats                            → collection stats
"""

import argparse
import logging
import os
import sys

from retriever_lib import (
    REPO_ROOT, PROJECT_DIR, VECTOR_DB_DIR,
    format_chroma_results, filter_by_threshold
)

# ── Model & Chroma: loaded once at startup ──────────────────────────
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

import chromadb
from chromadb.utils import embedding_functions
import uvicorn
from fastapi import FastAPI, Query

app = FastAPI(
    title="Project Memory Retriever",
    description="Semantic search over project documentation",
    version="2.0.0"
)

# Global state (initialized at startup)
collection = None


def init_model():
    """Load embedding model and connect to Chroma. Called once at startup."""
    global collection

    if not os.path.exists(VECTOR_DB_DIR):
        print(f"Error: Vector DB not found at {VECTOR_DB_DIR}")
        print("Run indexer.py first to build the index.")
        sys.exit(1)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-m3"
    )

    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    try:
        collection = client.get_collection(
            name="project-memory",
            embedding_function=ef
        )
    except ValueError:
        print("Error: No collection found. Run indexer.py first.")
        sys.exit(1)

    print(f"✅ Model loaded (BAAI/bge-m3)")
    print(f"✅ Chroma connected ({collection.count()} chunks)")


# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    k: int = Query(5, description="Number of results (1-50)"),
    threshold: float = Query(0.3, description="Minimum similarity score (0.0-1.0)")
):
    if k < 1 or k > 50:
        return {"error": "k must be between 1 and 50"}

    results = collection.query(query_texts=[q], n_results=k)
    formatted = format_chroma_results(results)
    formatted = filter_by_threshold(formatted, threshold)

    return {
        "query": q,
        "results_count": len(formatted),
        "results": formatted
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "collection_size": collection.count() if collection else 0
    }


@app.get("/stats")
def stats():
    if not collection:
        return {"error": "Not initialized"}

    # Get a sample of metadata to show file distribution
    all_results = collection.get(limit=1000)
    files = set()
    if all_results and all_results.get("metadatas"):
        for m in all_results["metadatas"]:
            f = m.get("file", "unknown")
            if f:
                files.add(f)

    return {
        "collection": "project-memory",
        "total_chunks": collection.count(),
        "source_files": sorted(files) if files else []
    }


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Start the retrieval server")
    parser.add_argument("--port", "-p", type=int, default=8000,
                        help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host to bind (default: 127.0.0.1)")
    args = parser.parse_args()

    init_model()
    print(f"\n🚀 Server ready at http://{args.host}:{args.port}")
    print(f"   API docs: http://{args.host}:{args.port}/docs")
    print(f"   Health:   http://{args.host}:{args.port}/health\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
