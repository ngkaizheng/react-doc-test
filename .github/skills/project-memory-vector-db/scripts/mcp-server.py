"""
MCP server for Project Memory Vector DB system.

Provides native MCP tools for the VS Code agent to search, read,
and update project memory — no shell commands needed.

VS Code manages the process lifecycle via stdio transport.
Install: pip install mcp[cli]
"""

import json
import logging
import os
import sys

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

from mcp.server.fastmcp import FastMCP

from retriever_lib import (
    REPO_ROOT, PROJECT_DIR, VECTOR_DB_DIR,
    format_chroma_results, filter_by_threshold
)
from memory import (
    read_memory, update_section, append_note, clear_completed,
    append_wiki_entry, append_learning_entry, get_doc_list,
    MEMORY_PATH
)

# ── Chroma + model: loaded once at startup ────────────────────────
import chromadb
from chromadb.utils import embedding_functions

collection = None


def init_model():
    """Load embedding model and connect to Chroma. Called once at startup."""
    global collection

    if not os.path.exists(VECTOR_DB_DIR):
        print("Warning: Vector DB not found. Run indexer.py first.", file=sys.stderr)
        return

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    try:
        collection = client.get_collection(
            name="project-memory",
            embedding_function=ef
        )
    except ValueError:
        print("Warning: No collection found. Run indexer.py first.", file=sys.stderr)


# ── FastMCP server ────────────────────────────────────────────────

mcp = FastMCP(
    "Project Memory",
    description="Semantic search and management of project documentation, working memory, and lessons learned."
)


# ── Resources ─────────────────────────────────────────────────────

@mcp.resource("memory://current")
def get_current_memory() -> str:
    """Current MEMORY.md content (working memory)."""
    return read_memory()


@mcp.resource("memory://index-status")
def get_index_status() -> str:
    """Vector index statistics."""
    if not collection:
        return json.dumps({"status": "not_initialized", "total_chunks": 0})
    try:
        count = collection.count()
        return json.dumps({"status": "ok", "total_chunks": count})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


# ── Tools ─────────────────────────────────────────────────────────

@mcp.tool()
def search_memory(query: str, top_k: int = 5, threshold: float = 0.3) -> str:
    """Semantic search over all project documentation.

    Returns relevant chunks with file path, heading, line range, score, and preview.
    Use the returned line_start/line_end with read_file to get full content.

    Args:
        query: Natural language search query.
        top_k: Number of results to return (1-50, default: 5).
        threshold: Minimum similarity score (0.0-1.0, default: 0.3).
    """
    if not collection:
        return json.dumps({"error": "Vector DB not initialized. Run indexer.py first."})

    if top_k < 1 or top_k > 50:
        return json.dumps({"error": "top_k must be between 1 and 50"})

    try:
        results = collection.query(query_texts=[query], n_results=top_k)
        formatted = format_chroma_results(results)
        formatted = filter_by_threshold(formatted, threshold)
        return json.dumps({
            "query": query,
            "results_count": len(formatted),
            "results": formatted
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_memory() -> str:
    """Read the current MEMORY.md (working memory) content."""
    return read_memory()


@mcp.tool()
def update_current_task(task: str) -> str:
    """Update the Current Task section in MEMORY.md.

    Args:
        task: Description of the current active task.
    """
    update_section("Current Task", task)
    return f"Current Task updated to: {task}"


@mcp.tool()
def append_memory_note(note: str) -> str:
    """Append a note to MEMORY.md (e.g., a discovery, blocker, or decision).

    Args:
        note: The note text to append.
    """
    append_note(note)
    return f"Note added to MEMORY.md"


@mcp.tool()
def clear_completed_tasks() -> str:
    """Clear the Completed section in MEMORY.md.
    Call this when starting a new feature cycle.
    """
    clear_completed()
    return "Completed section cleared."


@mcp.tool()
def add_learning(
    title: str,
    problem: str,
    root_cause: str,
    solution: str,
    key_takeaway: str
) -> str:
    """Add a lesson learned to LEARNING.md (appears at the top).

    Args:
        title: Short descriptive title of the lesson.
        problem: What went wrong or what needed solving.
        root_cause: Why it happened.
        solution: How it was fixed.
        key_takeaway: What to remember for next time.
    """
    append_learning_entry(title, problem, root_cause, solution, key_takeaway)
    return f"Lesson '{title}' added to LEARNING.md.\n\nRun refresh_index() to update the vector index."


@mcp.tool()
def add_wiki_entry(heading: str, content: str, section: str = "") -> str:
    """Add content to WIKI.md (project wiki / source of truth).

    If section is provided, the entry is added under that ## section.
    If section is empty, a new ## section is created with the heading.

    Args:
        heading: The ### sub-heading for this entry.
        content: The markdown content to add.
        section: Optional ## section name to add under.
    """
    section_name = section if section else None
    append_wiki_entry(heading, content, section_name)
    msg = f"Entry '{heading}' added to WIKI.md"
    if section:
        msg += f" under ## {section}"
    return msg + ".\n\nRun refresh_index() to update the vector index."


@mcp.tool()
def refresh_index() -> str:
    """Rebuild the Chroma vector index from all docs/ files.
    Call this after adding or modifying documentation to keep search results current.
    """
    try:
        import subprocess
        indexer_path = os.path.join(
            REPO_ROOT, ".github", "skills", "project-memory-vector-db", "scripts", "indexer.py"
        )
        result = subprocess.run(
            [sys.executable, indexer_path],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout.strip() or result.stderr.strip()
        # Reload collection after index
        init_model()
        count = collection.count() if collection else 0
        return f"Index rebuilt. Chroma now has {count} chunks.\n{output}"
    except subprocess.TimeoutExpired:
        return "Error: Indexer timed out after 60 seconds."
    except Exception as e:
        return f"Error refreshing index: {e}"


@mcp.tool()
def index_status() -> str:
    """Get the current state of the vector index.
    Returns number of indexed chunks and list of source files.
    """
    if not collection:
        return json.dumps({"status": "not_initialized", "total_chunks": 0})

    try:
        count = collection.count()
        # Get sample metadata to list source files
        all_results = collection.get(limit=1000)
        files = set()
        if all_results and all_results.get("metadatas"):
            for m in all_results["metadatas"]:
                f = m.get("file", "")
                if f:
                    files.add(f)

        return json.dumps({
            "status": "ok",
            "total_chunks": count,
            "source_files": sorted(files) if files else []
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


# ── Main ─────────────────────────────────────────────────────────

def main():
    """Start the MCP server. VS Code manages the process via stdio."""
    init_model()
    print("Project Memory MCP server starting...", file=sys.stderr)
    if collection:
        print(f"Chroma ready: {collection.count()} chunks", file=sys.stderr)
    else:
        print("Warning: Chroma not available. Run indexer.py first.", file=sys.stderr)

    # Run with stdio transport — VS Code handles lifecycle
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
