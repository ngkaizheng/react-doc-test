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
    format_chroma_results, format_m2m_results, filter_by_threshold,
    keyword_boost
)
from memory import (
    read_memory, update_working_memory as memory_update_working_memory,
    append_wiki_entry,
    update_wiki_entry as memory_update_wiki_entry,
    remove_wiki_entry as memory_remove_wiki_entry,
    expand_wiki_entry as memory_expand_wiki_entry,
    append_learning_entry, get_doc_list,
    MEMORY_PATH
)
# In-process indexer — no subprocess needed
from indexer import run_incremental_index, load_knowledge_sources, load_embedding_model_name

# ── Chroma + model: loaded once at startup ────────────────────────
import chromadb
from chromadb.utils import embedding_functions

collection = None


def init_model() -> str:
    """Load embedding model and connect to Chroma. Called once at startup.
    Reads the model name from knowledge-sources.json (configurable).

    Returns a status message indicating success or failure.
    """
    global collection

    if not os.path.exists(VECTOR_DB_DIR):
        msg = "Vector DB not found. Run indexer.py first."
        print(f"Warning: {msg}", file=sys.stderr)
        return msg

    model_name = load_embedding_model_name()
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    try:
        collection = client.get_collection(
            name="project-memory",
            embedding_function=ef
        )
        count = collection.count()
        return f"Chroma connected ({count} chunks) [model={model_name}]"
    except ValueError:
        msg = "No collection found. Run indexer.py first."
        print(f"Warning: {msg}", file=sys.stderr)
        return msg


# ── FastMCP server ────────────────────────────────────────────────

mcp = FastMCP(
    "Project Memory"
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
def search_memory(
    query: str,
    top_k: int = 5,
    threshold: float = 0.3,
    format: str = "m2m",
    source: str = "",
    keywords: str = ""
) -> str:
    """Semantic search over project documentation with optional source filtering and hybrid keyword boost.

    Returns relevant chunks with full content, similarity score, and
    nested metadata (source file, heading hierarchy, line range).
    Use the returned SRC:/LINES: to read_file for complete context.

    When format="m2m", returns a flat line-delimited string instead of
    JSON — optimized for AI agent token budgets.

    HYBRID SEARCH: When 'keywords' is provided, chunks containing those
    keywords get a score boost, so exact matches rank higher while
    semantic neighbors are still returned. Use this when you know
    specific terms (function names, error messages, config keys).

    SOURCE FILTER: When 'source' is provided, results are narrowed to
    only chunks from that knowledge source label (e.g., "Specifications",
    "Core Knowledge"). Run index_status() or check session context to
    see available source labels.

    Args:
        query: Natural language search query.
        top_k: Number of results to return (1-50, default: 5).
        threshold: Minimum similarity score (0.0-1.0, default: 0.3).
        format: Output format — "m2m" (default) or "json".
        source: Optional source label to filter by (e.g., "Core Knowledge").
                Uses the label from knowledge-sources.json.
        keywords: Optional keywords for hybrid boost — chunks containing
                  these words get ranked higher.
    """
    if not collection:
        return json.dumps({"error": "Vector DB not initialized. Run indexer.py first."})

    if top_k < 1 or top_k > 50:
        return json.dumps({"error": "top_k must be between 1 and 50"})

    if format not in ("json", "m2m"):
        return json.dumps({"error": "format must be 'json' or 'm2m'"})

    try:
        # Build Chroma where filter for source label
        where_filter = None
        if source:
            where_filter = {"source_label": source}

        # Request extra results so hybrid re-ranking has room
        fetch_k = top_k * 3 if keywords else top_k
        results = collection.query(
            query_texts=[query],
            n_results=fetch_k,
            where=where_filter
        )
        formatted = format_chroma_results(results)
        formatted = filter_by_threshold(formatted, threshold)

        # Hybrid keyword boost: re-rank with keyword match score
        if keywords:
            for r in formatted:
                boost = keyword_boost(r.get("content", ""), keywords)
                r["score"] = round(min(1.0, r["score"] + boost), 4)
            formatted.sort(key=lambda x: x["score"], reverse=True)
            formatted = formatted[:top_k]

        if format == "m2m":
            return format_m2m_results(query, formatted)

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
def update_working_memory(
    current_task: str = "",
    next_steps: str = "",
    blocked: str = "",
    append_note: str = "",
    clear_completed: bool = False
) -> str:
    """Update sections in MEMORY.md (working memory).

    Each parameter maps to a ## section in MEMORY.md.
    Pass a value to overwrite that section; leave empty to skip it.

    Examples:
      - Update current task:          update_working_memory(current_task="Implementing auth")
      - Update current + add a note:  update_working_memory(current_task="...", append_note="Found a bug in...")
      - Clear completed section:      update_working_memory(clear_completed=True)

    Args:
        current_task: Overwrites the ## Current Task section. Empty = skip.
        next_steps: Overwrites the ## Next Steps section. Empty = skip.
        blocked: Overwrites the ## Blocked section. Empty = skip.
        append_note: Appends a note to the bottom of MEMORY.md. Empty = skip.
        clear_completed: If True, empties the ## Completed section.
    """
    # Convert empty strings to None so the function knows which were explicitly provided
    result = memory_update_working_memory(
        current_task=current_task if current_task else None,
        next_steps=next_steps if next_steps else None,
        blocked=blocked if blocked else None,
        append_note_text=append_note if append_note else None,
        clear_completed_flag=clear_completed
    )
    return result + "\n\nUse get_memory() to see the updated content."


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
    Skips silently if a ### with the same heading already exists (use
    update_wiki_entry or expand_wiki_entry to modify existing entries).

    Args:
        heading: The ### sub-heading for this entry.
        content: The markdown content to add.
        section: Optional ## section name to add under.
    """
    section_name = section if section else None
    _text, action = append_wiki_entry(heading, content, section_name)
    if action == "skipped":
        msg = f"Skipped: '### {heading}' already exists under '## {section}'"
        msg += ". Use update_wiki_entry or expand_wiki_entry to modify it."
    elif action == "created":
        if section:
            msg = f"Created new section '## {section}' with entry '### {heading}'"
        else:
            msg = f"Created new section '## {heading}'"
    else:
        msg = f"Entry '### {heading}' added under '## {section}'"
    return msg + ".\n\nRun refresh_index() to update the vector index."


@mcp.tool()
def update_wiki_entry(heading: str, content: str, section: str = "") -> str:
    """Replace the content of an existing ### entry in WIKI.md.

    Args:
        heading: The ### sub-heading of the entry to update.
        content: The new markdown content (replaces existing content entirely).
        section: The ## section containing the entry.
    """
    if not section:
        return "Error: section is required for update_wiki_entry."
    _text, action = memory_update_wiki_entry(heading, content, section)
    if action == "not_found":
        return f"Entry '### {heading}' not found under '## {section}'."
    return f"Entry '### {heading}' under '## {section}' has been updated.\n\nRun refresh_index() to update the vector index."


@mcp.tool()
def remove_wiki_entry(heading: str, section: str = "") -> str:
    """Remove an entire ### entry block from WIKI.md.

    Args:
        heading: The ### sub-heading of the entry to remove.
        section: The ## section containing the entry.
    """
    if not section:
        return "Error: section is required for remove_wiki_entry."
    _text, action = memory_remove_wiki_entry(heading, section)
    if action == "not_found":
        return f"Entry '### {heading}' not found under '## {section}'."
    return f"Entry '### {heading}' removed from '## {section}'.\n\nRun refresh_index() to update the vector index."


@mcp.tool()
def expand_wiki_entry(heading: str, content: str, section: str = "") -> str:
    """Append additional content to an existing ### entry in WIKI.md.

    The new content is added after the existing entry content (does not
    replace anything). Use update_wiki_entry to replace entirely.

    Args:
        heading: The ### sub-heading of the entry to expand.
        content: The additional markdown content to append.
        section: The ## section containing the entry.
    """
    if not section:
        return "Error: section is required for expand_wiki_entry."
    _text, action = memory_expand_wiki_entry(heading, content, section)
    if action == "not_found":
        return f"Entry '### {heading}' not found under '## {section}'."
    return f"Content appended to '### {heading}' under '## {section}'.\n\nRun refresh_index() to update the vector index."


@mcp.tool()
def refresh_index() -> str:
    """Rebuild the Chroma vector index from all docs/ files.
    Call this after adding or modifying documentation to keep search results current.
    Runs in-process — reuses the already-loaded embedding model for maximum speed.
    """
    global collection
    try:
        # If collection wasn't initialized (e.g. inspector spawned a fresh process),
        # try initializing now
        if collection is None:
            init_model()
        result = run_incremental_index(collection=collection)
        col = result["collection"]
        # Update the global collection reference so future search_memory() calls work
        if col is not None:
            collection = col
        count = col.count() if col else 0
        return (
            f"Index rebuilt. Chroma now has {count} chunks.\n"
            f"  • {result['indexed']} files indexed\n"
            f"  • {result['skipped']} files skipped (unchanged)\n"
            f"  • {result['removed']} files removed"
        )
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


@mcp.tool()
def memory_stats() -> str:
    """Get detailed statistics about the vector index.

    Returns per-source chunk counts, file counts, total chunks,
    embedding model, and last indexed timestamp.

    Useful for understanding what knowledge is available and
    verifying that sources are properly indexed.
    """
    if not collection:
        return json.dumps({"status": "not_initialized"})

    try:
        count = collection.count()
        all_results = collection.get(limit=10000)

        # Aggregate by source_label
        sources_map: dict[str, dict] = {}
        files_set: set[str] = set()
        if all_results and all_results.get("metadatas"):
            for m in all_results["metadatas"]:
                label = m.get("source_label", "unknown")
                f = m.get("file", "")
                files_set.add(f)
                if label not in sources_map:
                    sources_map[label] = {"chunks": 0, "files": set()}
                sources_map[label]["chunks"] += 1
                if f:
                    sources_map[label]["files"].add(f)

        config = load_knowledge_sources()
        model = load_embedding_model_name()

        stats = {
            "status": "ok",
            "total_chunks": count,
            "total_files": len(files_set),
            "embedding_model": model,
            "last_indexed": None,
            "sources": {}
        }

        # Check manifest for last_indexed
        manifest_path = os.path.join(PROJECT_DIR, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path) as f:
                    mf = json.load(f)
                stats["last_indexed"] = mf.get("last_updated")
            except Exception:
                pass

        # Per-source breakdown
        for label, data in sorted(sources_map.items()):
            stats["sources"][label] = {
                "chunks": data["chunks"],
                "files": len(data["files"])
            }

        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})


# ── Main ─────────────────────────────────────────────────────────

def main():
    """Start the MCP server. VS Code manages the process via stdio."""
    status = init_model()
    print(f"Project Memory MCP server starting... [{status}]", file=sys.stderr)

    # Run with stdio transport — VS Code handles lifecycle
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
