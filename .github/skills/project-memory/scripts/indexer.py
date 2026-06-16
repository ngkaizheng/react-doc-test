"""
Stop hook script for Project Memory system.

Parses WIKI.md and LEARNING.md for H2 (##) and H3 (###) headings,
then rebuilds project-memory/index.json with section metadata
(keys, line ranges, keywords).

This runs automatically at the end of every agent session to
keep the knowledge index in sync with the actual file contents.
"""

import json
import os
import re
import sys

REPO_ROOT = os.getcwd()
PROJECT_MEMORY_DIR = os.path.join(REPO_ROOT, "project-memory")

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "our", "you", "your", "not", "no", "nor", "so", "very", "just",
    "about", "if", "then", "than", "also", "into", "over", "such"
}


def slugify(text: str) -> str:
    """Convert heading text to a URL-friendly key."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def is_comment_line(line: str) -> bool:
    """Check if a line is an HTML comment (<!-- ... -->)."""
    stripped = line.strip()
    return stripped.startswith("<!--") or stripped.startswith("-->") or "<!--" in stripped


def extract_keywords(heading_text: str, next_lines: list[str], max_words: int = 5) -> list[str]:
    """Extract meaningful keywords from a heading (case-deduplicated).
    Only uses the heading text — ignores following lines to avoid noise from comments."""
    seen = set()
    result = []

    # From heading — lowercase everything for dedup
    heading_words = re.findall(r'[a-zA-Z][a-z0-9]{2,}', heading_text)
    for w in heading_words:
        wl = w.lower()
        if wl not in STOP_WORDS and wl not in seen:
            seen.add(wl)
            result.append(wl)
            if len(result) >= max_words:
                break

    # From the first 1-2 following lines (skip comment lines)
    for line in next_lines[:2]:
        if line.strip().startswith('#') or is_comment_line(line):
            continue
        line_words = re.findall(r'[a-zA-Z][a-z0-9]{2,}', line)
        for w in line_words:
            wl = w.lower()
            if wl not in STOP_WORDS and wl not in seen and len(result) < max_words:
                seen.add(wl)
                result.append(wl)

    return result if result else [slugify(heading_text).replace('-', ' ')]


def parse_sections(filepath: str, label: str) -> dict:
    """Parse a markdown file and return section entries for the index.

    Indexes H2 (##) and H3 (###) headings.
    """
    sections = {}

    if not os.path.exists(filepath):
        return sections

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove trailing newlines for consistent handling
    lines = [line.rstrip('\n\r') for line in lines]

    current_key = None
    current_heading = None
    start_line = 1  # 1-based line numbers
    heading_level = 0

    for idx, line in enumerate(lines, start=1):
        match = re.match(r'^(#{2,3})\s+(.+)$', line)
        if match:
            # Close previous section
            if current_key and current_heading:
                end_line = idx - 1
                # Grab next lines for keyword extraction
                next_lines = lines[idx: idx + 3] if idx < len(lines) else []
                keywords = extract_keywords(current_heading, next_lines)
                sections[current_key] = {
                    "heading": current_heading,
                    "line_start": start_line,
                    "line_end": end_line,
                    "level": heading_level,
                    "keywords": keywords
                }

            # Start new section
            heading_level = len(match.group(1))  # 2 or 3
            current_heading = match.group(2).strip()
            current_key = slugify(current_heading)
            start_line = idx + 1

    # Close last section
    if current_key and current_heading:
        end_line = len(lines)
        sections[current_key] = {
            "heading": current_heading,
            "line_start": start_line,
            "line_end": end_line,
            "level": heading_level,
            "keywords": extract_keywords(current_heading, [])
        }

    return sections


def main():
    os.makedirs(PROJECT_MEMORY_DIR, exist_ok=True)

    wiki_path = os.path.join(PROJECT_MEMORY_DIR, "WIKI.md")
    learning_path = os.path.join(PROJECT_MEMORY_DIR, "LEARNING.md")
    index_path = os.path.join(PROJECT_MEMORY_DIR, "index.json")

    wiki_sections = parse_sections(wiki_path, "wiki")
    learning_sections = parse_sections(learning_path, "learning")

    index_data = {
        "last_updated": None,  # Will be set on first section added
        "wiki": wiki_sections,
        "learning": learning_sections
    }

    # Set timestamp if any sections exist
    if wiki_sections or learning_sections:
        from datetime import datetime, timezone
        index_data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # Print summary for logging
    wiki_count = len(wiki_sections)
    learning_count = len(learning_sections)
    print(f"[indexer] Index rebuilt: {wiki_count} wiki sections, {learning_count} learning sections")

    sys.exit(0)


if __name__ == "__main__":
    main()
