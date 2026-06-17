"""
File operations for Project Memory system.

Handles reading/writing MEMORY.md, WIKI.md, LEARNING.md with
section-aware updates. Used by mcp-server.py and available for
other scripts.
"""

import os
import re
from datetime import date
from typing import Optional

from retriever_lib import PROJECT_DIR

MEMORY_PATH = os.path.join(PROJECT_DIR, "MEMORY.md")
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
WIKI_PATH = os.path.join(DOCS_DIR, "WIKI.md")
LEARNING_PATH = os.path.join(DOCS_DIR, "LEARNING.md")


# ── MEMORY.md operations ──────────────────────────────────────────

def read_memory() -> str:
    """Read MEMORY.md content. Returns empty string if not found."""
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "# Working Memory\n\n## Current Task\n\n## Next Steps\n\n## Blocked\n\n## Completed\n"


def update_section(section: str, content: str) -> str:
    """Update a specific ## section in MEMORY.md. Creates section if missing."""
    text = read_memory()
    pattern = re.compile(rf'^(## {re.escape(section)})\s*$.*?(?=^## |\Z)', re.MULTILINE | re.DOTALL)
    replacement = f"## {section}\n{content}"

    if pattern.search(text):
        text = pattern.sub(replacement, text)
    else:
        text += f"\n\n{replacement}\n"

    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def append_note(note: str) -> str:
    """Append a note to the bottom of MEMORY.md."""
    text = read_memory()
    text += f"\n- {note}\n"
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def clear_completed() -> str:
    """Clear the Completed section (keep it empty)."""
    return update_section("Completed", "")


# ── WIKI.md operations ────────────────────────────────────────────

def append_wiki_entry(heading: str, content: str, section: Optional[str] = None) -> str:
    """Append content to WIKI.md.

    If section is given, appends under that ## section (or creates it).
    If section is None, creates a new ## section at the bottom.
    """
    text = _read_doc(WIKI_PATH, "# Project Wiki\n")

    if section:
        pattern = re.compile(rf'^(## {re.escape(section)})\s*$.*?(?=^## |\Z)', re.MULTILINE | re.DOTALL)
        entry = f"\n\n### {heading}\n{content}\n\n"
        if pattern.search(text):
            text = pattern.sub(lambda m: m.group(0).rstrip() + entry, text)
        else:
            text += f"\n\n## {section}\n\n### {heading}\n{content}\n\n"
    else:
        text += f"\n\n## {heading}\n{content}\n"

    _write_doc(WIKI_PATH, text)
    return text


def _read_doc(path: str, default: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return default


def _write_doc(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── LEARNING.md operations ────────────────────────────────────────

def append_learning_entry(title: str, problem: str, root_cause: str, solution: str, key_takeaway: str) -> str:
    """Append a lesson to the TOP of LEARNING.md (reverse chronological)."""
    today = date.today().isoformat()
    entry = (
        f"\n\n## {today}: {title}\n\n"
        f"**Problem:** {problem}\n\n"
        f"**Root Cause:** {root_cause}\n\n"
        f"**Solution:** {solution}\n\n"
        f"**Key Takeaway:** {key_takeaway}\n"
    )

    text = _read_doc(LEARNING_PATH, "# Lessons Learned\n")
    # Insert after the first line (the H1 heading)
    lines = text.split('\n', 1)
    text = lines[0] + entry + ('\n' + lines[1] if len(lines) > 1 else '')

    _write_doc(LEARNING_PATH, text)
    return text


# ── Utility ──────────────────────────────────────────────────────

def get_doc_list() -> list[dict]:
    """List all documentation files with basic metadata."""
    files = []
    docs_dir = DOCS_DIR
    if os.path.exists(docs_dir):
        for f in sorted(os.listdir(docs_dir)):
            path = os.path.join(docs_dir, f)
            if f.endswith(".md") and os.path.isfile(path):
                files.append({
                    "file": f"docs/{f}",
                    "size": os.path.getsize(path),
                    "modified": os.path.getmtime(path)
                })
    features_dir = os.path.join(docs_dir, "features")
    if os.path.exists(features_dir):
        for f in sorted(os.listdir(features_dir)):
            path = os.path.join(features_dir, f)
            if f.endswith(".md") and os.path.isfile(path):
                files.append({
                    "file": f"docs/features/{f}",
                    "size": os.path.getsize(path),
                    "modified": os.path.getmtime(path)
                })
    return files
