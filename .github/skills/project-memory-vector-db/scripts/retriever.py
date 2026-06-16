"""
On-demand retriever for Project Memory Vector DB system.

Called by the agent when it needs to find relevant knowledge.
Embeds the query using sentence-transformers, searches Chroma,
and returns the most similar chunks as JSON.

Usage:
    python retriever.py --query "How does payment retry work?" --top-k 5
    python retriever.py --query "JWT authentication" --top-k 3 --threshold 0.5
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.getcwd()
PROJECT_DIR = os.path.join(REPO_ROOT, "project-memory-vector-db")
VECTOR_DB_DIR = os.path.join(PROJECT_DIR, "vector-db")
MANIFEST_PATH = os.path.join(PROJECT_DIR, "manifest.json")


def get_collection():
    """Get the Chroma collection (lazy import)."""
    import chromadb
    from chromadb.utils import embedding_functions

    if not os.path.exists(VECTOR_DB_DIR):
        print(json.dumps({"error": "Vector database not found. Run indexer.py first."}))
        sys.exit(1)

    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    try:
        collection = client.get_collection(
            name="project-memory",
            embedding_function=ef
        )
        return collection
    except ValueError:
        print(json.dumps({"error": "No documents indexed yet. Run indexer.py first."}))
        sys.exit(1)


def truncate_preview(text: str, max_chars: int = 200) -> str:
    """Truncate text to a preview length, preserving whole words."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Cut at last space to avoid mid-word
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def format_results(results, top_k: int) -> list[dict]:
    """Format Chroma results into a clean JSON structure."""
    formatted = []
    if not results or not results["ids"] or not results["ids"][0]:
        return formatted

    for i in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][i]
        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
        distance = results["distances"][0][i] if results.get("distances") else 0.0
        document = results["documents"][0][i] if results.get("documents") else ""

        # Cosine distance → similarity score (1 = identical)
        score = round(1.0 - distance, 4)

        formatted.append({
            "id": chunk_id,
            "score": score,
            "file": metadata.get("file", ""),
            "heading": metadata.get("heading", ""),
            "parent_heading": metadata.get("parent_heading", ""),
            "line_start": metadata.get("line_start", 0),
            "line_end": metadata.get("line_end", 0),
            "preview": truncate_preview(document, 300)
        })

    return formatted


def main():
    parser = argparse.ArgumentParser(description="Semantic search over project memory")
    parser.add_argument("--query", "-q", type=str, required=True,
                        help="Search query (natural language)")
    parser.add_argument("--top-k", "-k", type=int, default=5,
                        help="Number of results to return (default: 5)")
    parser.add_argument("--threshold", "-t", type=float, default=0.0,
                        help="Minimum similarity threshold (0.0-1.0, default: 0.0)")
    args = parser.parse_args()

    # Validate
    if args.top_k < 1 or args.top_k > 50:
        print(json.dumps({"error": "top-k must be between 1 and 50"}))
        sys.exit(1)

    collection = get_collection()

    # Query Chroma
    results = collection.query(
        query_texts=[args.query],
        n_results=args.top_k
    )

    formatted = format_results(results, args.top_k)

    # Filter by threshold if any
    if args.threshold > 0.0:
        formatted = [r for r in formatted if r["score"] >= args.threshold]

    output = {
        "query": args.query,
        "results_count": len(formatted),
        "results": formatted
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
