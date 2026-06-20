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

from retriever_lib import PROJECT_DIR, REPO_ROOT

MEMORY_PATH = os.path.join(PROJECT_DIR, "MEMORY.md")
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
WIKI_PATH = os.path.join(DOCS_DIR, "WIKI.md")
LEARNING_PATH = os.path.join(DOCS_DIR, "LEARNING.md")
KNOWLEDGE_SOURCES_PATH = os.path.join(PROJECT_DIR, "knowledge-sources.json")


# ── MEMORY.md operations ──────────────────────────────────────────

def read_memory() -> str:
    """Read MEMORY.md content. Returns empty string if not found."""
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "# WM\n\n## [CT]\n\n## [NS]\n\n## [BL]\n\n## [CM]\n"


def _strip_code_blocks(text: str) -> str:
    """Replace fenced code blocks with placeholders to avoid matching inside them."""
    return re.sub(r'```.*?```', '{{{CODE_BLOCK}}}', text, flags=re.DOTALL)


def update_section(section: str, content: str) -> str:
    """Update a specific ## section in MEMORY.md. Creates section if missing."""
    text = read_memory()
    # Strip code blocks to prevent matching `## ` inside them
    safe_text = _strip_code_blocks(text)
    pattern = re.compile(rf'^(## {re.escape(section)})\s*$.*?(?=^## |\Z)', re.MULTILINE | re.DOTALL)
    # Ensure content has trailing newlines so next section doesn't bleed into it
    replacement = f"## {section}\n{content}\n\n"

    if pattern.search(safe_text):
        text = pattern.sub(replacement, text)
    else:
        text += f"\n\n## {section}\n{content}\n"

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
    return update_section("[CM]", "")


def update_working_memory(
    current_task: Optional[str] = None,
    next_steps: Optional[str] = None,
    blocked: Optional[str] = None,
    append_note_text: Optional[str] = None,
    clear_completed_flag: bool = False
) -> str:
    """Update multiple MEMORY.md sections in a single call.

    Args:
        current_task: If set, replaces the ## Current Task section.
        next_steps: If set, replaces the ## Next Steps section.
        blocked: If set, replaces the ## Blocked section.
        append_note_text: If set, appends a note to the bottom.
        clear_completed_flag: If True, empties the ## Completed section.

    Returns:
        A human-readable summary of what was updated.
    """
    changes = []

    if current_task is not None:
        update_section("[CT]", current_task)
        changes.append("current_task updated")

    if next_steps is not None:
        update_section("[NS]", next_steps)
        changes.append("next_steps updated")

    if blocked is not None:
        update_section("[BL]", blocked)
        changes.append("blocked updated")

    if clear_completed_flag:
        clear_completed()
        changes.append("completed cleared")

    if append_note_text is not None:
        append_note(append_note_text)
        changes.append("note appended")

    if not changes:
        return "No changes requested — pass at least one parameter."

    return "MEMORY.md: " + "; ".join(changes) + "."


# ── WIKI.md operations ────────────────────────────────────────────

def append_wiki_entry(heading: str, content: str, section: Optional[str] = None) -> tuple[str, str]:
    """Append content to WIKI.md.

    If section is given, appends under that ## section (or creates it).
    If section is None, creates a new ## section at the bottom.

    Guards against duplicate entries: if a ### heading with the same name
    already exists under the target ## section, it is skipped.

    Returns:
        tuple[str, str]: (updated text, action: "added" | "skipped" | "created")
    """
    text = _read_doc(WIKI_PATH, "# Project Wiki\n")

    if section:
        # Check for duplicate ### heading under this section
        dup_pattern = re.compile(
            rf'^## {re.escape(section)}\s*$.*?^### {re.escape(heading)}\s*$',
            re.MULTILINE | re.DOTALL
        )
        if dup_pattern.search(text):
            return text, "skipped"  # Entry already exists

        safe_text = _strip_code_blocks(text)
        pattern = re.compile(rf'^(## {re.escape(section)})\s*$.*?(?=^## |\Z)', re.MULTILINE | re.DOTALL)
        entry = f"\n\n### {heading}\n{content}\n\n"
        if pattern.search(safe_text):
            text = pattern.sub(lambda m: m.group(0).rstrip() + entry, text)
            action = "added"
        else:
            text += f"\n\n## {section}\n\n### {heading}\n{content}\n\n"
            action = "created"
    else:
        # Check for duplicate ## section
        dup_pattern = re.compile(rf'^## {re.escape(heading)}\s*$', re.MULTILINE)
        if dup_pattern.search(text):
            return text, "skipped"  # Section already exists
        text += f"\n\n## {heading}\n{content}\n"
        action = "created"

    _write_doc(WIKI_PATH, text)
    return text, action


def _find_entry_block(text: str, section: str, heading: str) -> tuple[Optional[re.Match], str]:
    """Find a ### entry block under a ## section.

    Returns (match, full_section_text) where match covers from ### to next ###/##/EOF.
    The entry pattern: ^### {heading}$ followed by content up to next ### or ## or EOF.
    """
    safe = _strip_code_blocks(text)
    # First locate the ## section
    sec_pat = re.compile(
        rf'^## {re.escape(section)}\s*$(.*?)(?=^## |\Z)',
        re.MULTILINE | re.DOTALL
    )
    sec_match = sec_pat.search(safe)
    if not sec_match:
        return None, text

    section_content = sec_match.group(1)
    # Now find the ### heading within the section
    entry_pat = re.compile(
        rf'^(### {re.escape(heading)})\s*$(.*?)(?=^### |^## |\Z)',
        re.MULTILINE | re.DOTALL
    )
    entry_match = entry_pat.search(section_content)
    if not entry_match:
        return None, text

    return entry_match, text


def update_wiki_entry(heading: str, content: str, section: str) -> tuple[str, str]:
    """Replace the content of an existing ### entry under a ## section.

    Returns:
        tuple[str, str]: (updated text, action: "updated" | "not_found")
    """
    text = _read_doc(WIKI_PATH, "# Project Wiki\n")
    entry_match, text = _find_entry_block(text, section, heading)
    if not entry_match:
        return text, "not_found"

    # Replace everything after `### Heading\n` to the next boundary with new content
    full_match_text = entry_match.group(0)
    # Preserve the original trailing whitespace/blank lines
    trailing = ''
    stripped = full_match_text.rstrip()
    if len(stripped) < len(full_match_text):
        trailing = full_match_text[len(stripped):]
    # The match has `### Heading\n...content...`
    first_line_end = full_match_text.index('\n') if '\n' in full_match_text else len(full_match_text)
    header_line = full_match_text[:first_line_end]
    new_block = header_line + '\n' + content + trailing
    text = text.replace(full_match_text, new_block, 1)

    _write_doc(WIKI_PATH, text)
    return text, "updated"


def remove_wiki_entry(heading: str, section: str) -> tuple[str, str]:
    """Remove an entire ### entry block under a ## section.

    Returns:
        tuple[str, str]: (updated text, action: "removed" | "not_found")
    """
    text = _read_doc(WIKI_PATH, "# Project Wiki\n")
    entry_match, text = _find_entry_block(text, section, heading)
    if not entry_match:
        return text, "not_found"

    # Remove the entire ### block plus preceding blank lines
    full_match = entry_match.group(0)
    # Strip leading newlines so we don't leave gaps
    stripped = '\n' + full_match.strip()
    idx = text.find(stripped)
    if idx >= 0:
        text = text[:idx] + '\n' + text[idx + len(stripped):]
    else:
        text = text.replace(full_match, '', 1)

    _write_doc(WIKI_PATH, text)
    return text, "removed"


def expand_wiki_entry(heading: str, content: str, section: str) -> tuple[str, str]:
    """Append additional content to an existing ### entry under a ## section.

    Returns:
        tuple[str, str]: (updated text, action: "expanded" | "not_found")
    """
    text = _read_doc(WIKI_PATH, "# Project Wiki\n")
    entry_match, text = _find_entry_block(text, section, heading)
    if not entry_match:
        return text, "not_found"

    full_match = entry_match.group(0)
    # Append new content at the end of the entry (before the trailing newline)
    new_block = full_match.rstrip() + '\n' + content + '\n'
    text = text.replace(full_match, new_block, 1)

    _write_doc(WIKI_PATH, text)
    return text, "expanded"


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
    # Find the first non-blank, non-comment line (the H1 heading)
    lines = text.split('\n')
    first_content_idx = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('<!--'):
            first_content_idx = i
            break
    # Insert entry after the first content line
    before = '\n'.join(lines[:first_content_idx + 1])
    after = '\n'.join(lines[first_content_idx + 1:])
    text = before + entry + ('\n' + after if after.strip() else '')

    _write_doc(LEARNING_PATH, text)
    return text


# ── Utility ──────────────────────────────────────────────────────

def get_doc_list() -> list[dict]:
    """List all documentation files from configured knowledge sources.

    Reads knowledge-sources.json to discover files, falling back to
    the legacy docs/ directory if the config doesn't exist.
    """
    import fnmatch
    import json

    files = []

    # Try loading from knowledge-sources.json
    if os.path.exists(KNOWLEDGE_SOURCES_PATH):
        try:
            with open(KNOWLEDGE_SOURCES_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, KeyError):
            config = {}

        for source in config.get("sources", []):
            source_path = source.get("path", "")
            patterns = source.get("patterns", ["*.md"])
            recursive = source.get("recursive", True)

            abs_path = source_path if os.path.isabs(source_path) else os.path.join(REPO_ROOT, source_path)
            if not os.path.exists(abs_path):
                continue

            label = source.get("label", source_path)

            if os.path.isfile(abs_path):
                if any(fnmatch.fnmatch(os.path.basename(abs_path), p) for p in patterns):
                    files.append({
                        "file": os.path.relpath(abs_path, REPO_ROOT).replace(os.sep, '/'),
                        "size": os.path.getsize(abs_path),
                        "modified": os.path.getmtime(abs_path),
                        "source": label
                    })
                continue

            if recursive:
                for root, _dirs, filenames in os.walk(abs_path):
                    for filename in sorted(filenames):
                        if any(fnmatch.fnmatch(filename, p) for p in patterns):
                            fpath = os.path.join(root, filename)
                            files.append({
                                "file": os.path.relpath(fpath, REPO_ROOT).replace(os.sep, '/'),
                                "size": os.path.getsize(fpath),
                                "modified": os.path.getmtime(fpath),
                                "source": label
                            })
            else:
                with os.scandir(abs_path) as it:
                    for entry in sorted(it, key=lambda e: e.name):
                        if entry.is_file() and any(fnmatch.fnmatch(entry.name, p) for p in patterns):
                            files.append({
                                "file": os.path.relpath(entry.path, REPO_ROOT).replace(os.sep, '/'),
                                "size": os.path.getsize(entry.path),
                                "modified": os.path.getmtime(entry.path),
                                "source": label
                            })
        return files

    # Fallback: legacy docs/ directory
    if os.path.exists(DOCS_DIR):
        for f in sorted(os.listdir(DOCS_DIR)):
            path = os.path.join(DOCS_DIR, f)
            if f.endswith(".md") and os.path.isfile(path):
                files.append({
                    "file": f"docs/{f}",
                    "size": os.path.getsize(path),
                    "modified": os.path.getmtime(path)
                })
        features_dir = os.path.join(DOCS_DIR, "features")
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
