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


def format_chroma_results(results) -> list[dict]:
    """Format Chroma query results into standard RAG format.

    Uses the industry-standard Document pattern (used by LangChain,
    LlamaIndex, MLflow, Azure AI Search):

        {
            "id": "<unique chunk id>",
            "score": 0.9234,
            "content": "Full text...",      # Full, untruncated content
            "metadata": {                     # All metadata nested together
                "source": "path/to/file.md",
                "heading": "...",
                "parent_heading": "...",
                "line_start": 12,
                "line_end": 35
            }
        }

    This separates content (for LLM prompt injection) from metadata
    (for citations, filtering, and source tracking).
    """
    formatted = []
    if not results or not results.get("ids") or not results["ids"]:
        return formatted

    ids_list = results["ids"]
    if not ids_list or not ids_list[0]:
        return formatted

    for i in range(len(ids_list[0])):
        chunk_id = ids_list[0][i]
        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
        distance = results["distances"][0][i] if results.get("distances") else 0.0
        document = results["documents"][0][i] if results.get("documents") else ""

        score = round(1.0 - distance, 4)

        formatted.append({
            "id": chunk_id,
            "score": score,
            "content": document,  # Full content — LLM needs complete text
            "metadata": {
                "source": meta.get("file", ""),
                "heading": meta.get("heading", ""),
                "parent_heading": meta.get("parent_heading", ""),
                "line_start": meta.get("line_start", 0),
                "line_end": meta.get("line_end", 0)
            }
        })

    return formatted


def filter_by_threshold(results: list[dict], threshold: float) -> list[dict]:
    """Filter results below a similarity threshold."""
    if threshold <= 0.0:
        return results
    return [r for r in results if r["score"] >= threshold]


def truncate_preview(text: str, max_chars: int = 200) -> str:
    """Truncate text to a preview length, preserving whole words.

    Note: This is only used for the CLI preview display.
    The actual 'content' field always returns the full text.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def print_json_output(query: str, results: list[dict]):
    """Print formatted JSON output to stdout.

    Includes a human-readable 'preview' alongside the full 'content'
    for CLI display convenience.
    """
    # Add preview for CLI readability without modifying original chunks
    display_results = []
    for r in results:
        display = {**r}
        display["preview"] = truncate_preview(r.get("content", ""), 300)
        display_results.append(display)

    output = {
        "query": query,
        "results_count": len(results),
        "results": display_results
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def die(error_message: str):
    """Print error JSON and exit."""
    print(json.dumps({"error": error_message}))
    sys.exit(1)
