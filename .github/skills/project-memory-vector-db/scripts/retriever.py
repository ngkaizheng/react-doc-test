"""
On-demand retriever for Project Memory Vector DB system.

Two modes:
  1. Direct (default): Loads model, queries Chroma directly.
  2. Server: Delegates to a running retriever-server.py via HTTP.

Usage:
    python retriever.py --query "How does payment retry work?"
    python retriever.py --server --query "JWT auth" --port 8000
"""

import argparse
import json
import os
import sys
from urllib.request import urlopen, Request
from urllib.parse import urlencode

from retriever_lib import (
    REPO_ROOT, PROJECT_DIR, VECTOR_DB_DIR,
    format_chroma_results, filter_by_threshold,
    print_json_output, die
)


def get_collection():
    """Get the Chroma collection (lazy import, direct mode only)."""
    import logging
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

    import chromadb
    from chromadb.utils import embedding_functions

    if not os.path.exists(VECTOR_DB_DIR):
        die("Vector database not found. Run indexer.py first.")

    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    try:
        return client.get_collection(
            name="project-memory",
            embedding_function=ef
        )
    except ValueError:
        die("No documents indexed yet. Run indexer.py first.")


def search_server(query: str, top_k: int, threshold: float, port: int):
    """Delegate search to the running retriever-server."""
    params = urlencode({"q": query, "k": top_k, "threshold": threshold})
    url = f"http://127.0.0.1:{port}/search?{params}"

    try:
        req = Request(url)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except ConnectionRefusedError:
        die(f"Cannot connect to server at port {port}. Is retriever-server.py running?")
    except Exception as e:
        die(f"Server request failed: {e}")

    print_json_output(query, data.get("results", []))
    sys.exit(0)


def search_direct(query: str, top_k: int, threshold: float):
    """Search by loading the model and querying Chroma directly."""
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)
    formatted = format_chroma_results(results)
    formatted = filter_by_threshold(formatted, threshold)
    print_json_output(query, formatted)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Semantic search over project memory"
    )
    parser.add_argument("--query", "-q", type=str, required=True,
                        help="Search query (natural language)")
    parser.add_argument("--top-k", "-k", type=int, default=5,
                        help="Number of results (default: 5)")
    parser.add_argument("--threshold", "-t", type=float, default=0.3,
                        help="Minimum similarity threshold (default: 0.3)")
    parser.add_argument("--server", "-s", action="store_true",
                        help="Use server mode (connect to retriever-server)")
    parser.add_argument("--port", "-p", type=int, default=8000,
                        help="Server port (default: 8000, used with --server)")
    args = parser.parse_args()

    if args.top_k < 1 or args.top_k > 50:
        die("top-k must be between 1 and 50")

    if args.server:
        search_server(args.query, args.top_k, args.threshold, args.port)
    else:
        search_direct(args.query, args.top_k, args.threshold)


if __name__ == "__main__":
    main()
