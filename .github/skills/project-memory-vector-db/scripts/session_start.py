"""
SessionStart hook script for Project Memory Vector DB system.

Reads MEMORY.md and knowledge-sources.json, outputs a systemMessage
with dynamic source listing so the agent starts every session with
full working context.
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../.."
    )
)
PROJECT_DIR = os.path.join(REPO_ROOT, "project-memory-vector-db")
MEMORY_PATH = os.path.join(PROJECT_DIR, "MEMORY.md")
MANIFEST_PATH = os.path.join(PROJECT_DIR, "manifest.json")
KNOWLEDGE_SOURCES_PATH = os.path.join(PROJECT_DIR, "knowledge-sources.json")
RETRIEVER_PATH = os.path.join(
    REPO_ROOT, ".github", "skills", "project-memory-vector-db", "scripts", "retriever.py"
)
TEMPLATE_DIR = os.path.join(
    REPO_ROOT, ".github", "skills", "project-memory-vector-db", "scripts", "templates"
)


def read_or_template(filepath: str, template_name: str) -> str:
    """Read file if it exists, otherwise return the template content."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    # Fall back to template
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"# {template_name.replace('.md', '')}\n\n_(Not yet initialized — run `init.py` to create templates.)_"


def load_knowledge_sources() -> list[dict]:
    """Load configured knowledge sources from knowledge-sources.json."""
    default_sources = [
        {"label": "Core Knowledge", "path": "project-memory-vector-db/docs",
         "patterns": ["*.md"], "description": "WIKI.md, LEARNING.md, and feature documentation"},
    ]
    if not os.path.exists(KNOWLEDGE_SOURCES_PATH):
        return default_sources
    try:
        with open(KNOWLEDGE_SOURCES_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("sources", default_sources)
    except (json.JSONDecodeError, KeyError):
        return default_sources


def format_system_message(memory_content: str, has_index: bool) -> str:
    """Wrap memory content with usage instructions for the agent."""
    sources = load_knowledge_sources()
    parts = []

    parts.append("=== 🧠 PROJECT MEMORY SYSTEM (Vector DB) ===")
    parts.append("You have a semantic memory system in `project-memory-vector-db/`.")
    parts.append("")
    parts.append("📚 **Knowledge Sources** (configured in `knowledge-sources.json`):")
    for src in sources:
        label = src.get("label", src.get("path", "?"))
        desc = src.get("description", "")
        patterns = ", ".join(src.get("patterns", ["*"]))
        parts.append(f"  • **{label}** — {desc} ({patterns})")
    parts.append("")
    parts.append("🔍 **MCP TOOLS AVAILABLE** (Use FIRST before grep/file search)")
    parts.append("This project has an MCP server. Use these native tools:")
    parts.append("  • `search_memory(query, top_k, threshold)` — ⭐ ALWAYS USE THIS FIRST")
    parts.append("    when you need project knowledge. It finds semantically related content")
    parts.append("    that keyword search misses entirely.")
    parts.append("  • `get_memory()` — Read current MEMORY.md")
    parts.append("  • `update_working_memory(current_task, next_steps, blocked, append_note, clear_completed)` — Update any MEMORY.md section")
    parts.append("  • `add_learning(title, problem, root_cause, solution, key_takeaway)` — Document a fix")
    parts.append("  • `add_wiki_entry(heading, content, section)` — Add new entry (skips if duplicate)")
    parts.append("  • `update_wiki_entry(heading, content, section)` — Replace an existing entry")
    parts.append("  • `expand_wiki_entry(heading, content, section)` — Append to an existing entry")
    parts.append("  • `remove_wiki_entry(heading, section)` — Delete an entry")
    parts.append("  • `refresh_index()` — Sync vector index after doc changes")
    parts.append("  • `index_status()` — Check vector DB health")
    parts.append("")
    parts.append("⚠️ **RETRIEVAL PRIORITY: search_memory() → grep_search()**")
    parts.append("Only fall back to grep_search / file_search if search_memory() returns nothing useful.")
    parts.append("")
    parts.append("🔄 **FALLBACK CLI** (if MCP is unavailable):")
    parts.append(f"  python {RETRIEVER_PATH} --query \"<your question>\" --top-k 5")
    parts.append("")

    if has_index:
        parts.append("✅ Knowledge base has indexed documents. Vector search is ready.")
    else:
        parts.append("⚠️  No documents indexed yet. Run the indexer to add docs/ files to the vector DB.")

    parts.append("")
    parts.append("")
    parts.append("=== 📋 MEMORY.md (Working Memory — Read & Update) ===")
    parts.append(memory_content)

    return "\n".join(parts)


def main():
    memory_content = read_or_template(MEMORY_PATH, "MEMORY.md")
    has_index = os.path.exists(MANIFEST_PATH)

    system_message = format_system_message(memory_content, has_index)

    output = {"systemMessage": system_message}
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
