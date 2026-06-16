"""
SessionStart hook script for Project Memory system.

Reads MEMORY.md and outputs it as a systemMessage so the agent
starts every session with full working context.
"""

import json
import os
import sys

REPO_ROOT = os.getcwd()
MEMORY_PATH = os.path.join(REPO_ROOT, "project-memory", "MEMORY.md")
INDEX_PATH = os.path.join(REPO_ROOT, "project-memory", "index.json")
TEMPLATE_DIR = os.path.join(
    REPO_ROOT, ".github", "skills", "project-memory", "scripts", "templates"
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


def format_system_message(memory_content: str, index_exists: bool) -> str:
    """Wrap memory content with usage instructions for the agent."""
    parts = []

    parts.append(
        "=== 🧠 PROJECT MEMORY SYSTEM ==="
    )
    parts.append(
        "You have a project memory system with these files in `project-memory/`:"
    )
    parts.append("- MEMORY.md (loaded below) — Working memory: current tasks, active problems, next steps.")
    parts.append("- WIKI.md — Source of truth: architecture, decisions, standards. Read sections on-demand via the index.")
    parts.append("- LEARNING.md — Lessons learned: bugs, edge cases, non-obvious fixes. Read sections on-demand via the index.")
    parts.append("- index.json — Section index for WIKI.md and LEARNING.md. Browse this first to find relevant sections.")
    parts.append("")

    if index_exists:
        parts.append("📋 An index of available knowledge sections exists in `project-memory/index.json`.")
        parts.append("   When you need architectural context or troubleshooting knowledge, read the index first,")
        parts.append("   then use `read_file` with the line ranges specified in the index.")
    else:
        parts.append("⚠️  No index.json found. Run the indexer to create one after WIKI.md or LEARNING.md have content.")

    parts.append("")
    parts.append("")

    # Append MEMORY.md content
    parts.append("=== 📋 MEMORY.md (Working Memory — Read & Update) ===")
    parts.append(memory_content)

    return "\n".join(parts)


def main():
    memory_content = read_or_template(MEMORY_PATH, "MEMORY.md")
    index_exists = os.path.exists(INDEX_PATH)

    system_message = format_system_message(memory_content, index_exists)

    output = {
        "systemMessage": system_message
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
