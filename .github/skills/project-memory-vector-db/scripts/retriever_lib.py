"""
Shared utilities for the Project Memory Vector DB retrieval system.

Used by both retriever.py (CLI) and retriever-server.py (FastAPI).
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
PROJECT_DIR = os.path.join(REPO_ROOT, "project-memory-vector-db")
VECTOR_DB_DIR = os.path.join(PROJECT_DIR, "vector-db")


def m2m_compress(text: str) -> str:
    """Strip structural markdown waste without altering semantic content.

    Safe for preserving embedding context — keeps full sentences, bold
    markers, and bullet syntax. Only removes zero-value overhead.

    Removes:
        - HTML comments (<!-- ... -->)
    Collapses:
        - 3+ consecutive newlines to 2
        - Leading/trailing whitespace per line
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(l.strip() for l in text.split('\n'))
    return text.strip()


def format_m2m_results(query: str, results: list[dict]) -> str:
    """Format search results as flat, line-delimited M2M string.

    Optimized for AI agent consumption — no JSON nesting overhead.
    Each result is a 5-line block separated by '---'.

    Uses pre-computed compact_content from metadata when available,
    falling back to full content for non-compacted chunks.
    """
    blocks = []
    for r in results:
        meta = r.get("metadata", {})
        text = r.get("compact_content", r.get("content", ""))

        # Breadcrumb PATH: "Parent > Heading" or just "Heading" if top-level
        parent = meta.get("parent_heading", "")
        heading = meta.get("heading", "")
        path = f"{parent} > {heading}" if parent else heading

        # Line range
        ls = meta.get("line_start", 0)
        le = meta.get("line_end", 0)
        lines = f"{ls}-{le}" if ls and le else ""

        block = (
            f"ID: {r['id']}\n"
            f"SCORE: {r['score']}\n"
            f"SRC: {meta.get('source', '')}\n"
            f"PATH: {path}\n"
            f"LINES: {lines}\n"
            f"TEXT: {text}\n"
            "---"
        )
        blocks.append(block)
    return "\n".join(blocks)


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

        # Forward compact_content from Chroma metadata if present
        compact = meta.get("compact_content", "")
        if not compact:
            compact = ""  # explicit empty for chunks with only HTML comments etc.

        formatted.append({
            "id": chunk_id,
            "score": score,
            "content": document,  # Full content — LLM needs complete text
            "compact_content": compact,  # M2M-lean variant for format="m2m"
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
