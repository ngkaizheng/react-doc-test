"""
SessionStart hook script for Project Memory Vector DB system.

Reads MEMORY.md and outputs it as a systemMessage so the agent
starts every session with full working context. Also informs the
agent about vector search capability.
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


def format_system_message(memory_content: str, has_index: bool) -> str:
    """Wrap memory content with usage instructions for the agent."""
    parts = []

    parts.append("=== 🧠 PROJECT MEMORY SYSTEM (Vector DB) ===")
    parts.append("You have a semantic memory system in `project-memory-vector-db/`:")
    parts.append("- MEMORY.md (loaded below) — Working memory: current tasks, active problems.")
    parts.append("- docs/WIKI.md — Source of truth: architecture, decisions, standards.")
    parts.append("- docs/LEARNING.md — Lessons learned: bugs, edge cases, fixes.")
    parts.append("- docs/features/ — Feature documentation (may have multiple files).")
    parts.append("")
    parts.append("🔍 **MCP TOOLS AVAILABLE** (Recommended)")
    parts.append("This project has an MCP server registered in `.vscode/mcp.json`.")
    parts.append("Use these native tools instead of shell commands:")
    parts.append("  • `search_memory(query, top_k, threshold)` — Semantic search over all docs")
    parts.append("  • `get_memory()` — Read current MEMORY.md")
    parts.append("  • `update_current_task(task)` — Update what you're working on")
    parts.append("  • `append_memory_note(note)` — Save a quick note")
    parts.append("  • `add_learning(title, problem, root_cause, solution, key_takeaway)` — Document a fix")
    parts.append("  • `add_wiki_entry(heading, content, section)` — Record a decision")
    parts.append("  • `refresh_index()` — Sync vector index after doc changes")
    parts.append("  • `index_status()` — Check vector DB health")
    parts.append("")
    parts.append("🔄 **FALLBACK** (if MCP is unavailable):")
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
