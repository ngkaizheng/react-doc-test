"""
Shared utilities for the Project Memory Vector DB retrieval system.

Used by both retriever.py (CLI) and retriever-server.py (FastAPI).
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
PROJECT_DIR = os.path.join(REPO_ROOT, "project-memory-vector-db")
VECTOR_DB_DIR = os.path.join(PROJECT_DIR, "vector-db")


def truncate_preview(text: str, max_chars: int = 200) -> str:
    """Truncate text to a preview length, preserving whole words."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def format_chroma_results(results) -> list[dict]:
    """Format Chroma query results into clean JSON structures."""
    formatted = []
    if not results or not results.get("ids") or not results["ids"]:
        return formatted

    ids_list = results["ids"]
    if not ids_list or not ids_list[0]:
        return formatted

    for i in range(len(ids_list[0])):
        chunk_id = ids_list[0][i]
        metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
        distance = results["distances"][0][i] if results.get("distances") else 0.0
        document = results["documents"][0][i] if results.get("documents") else ""

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


def filter_by_threshold(results: list[dict], threshold: float) -> list[dict]:
    """Filter results below a similarity threshold."""
    if threshold <= 0.0:
        return results
    return [r for r in results if r["score"] >= threshold]


def print_json_output(query: str, results: list[dict]):
    """Print formatted JSON output to stdout."""
    output = {
        "query": query,
        "results_count": len(results),
        "results": results
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def die(error_message: str):
    """Print error JSON and exit."""
    print(json.dumps({"error": error_message}))
    sys.exit(1)
