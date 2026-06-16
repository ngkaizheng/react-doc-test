"""
Initialization script for Project Memory system.

Creates:
  - project-memory/ directory with MEMORY.md, WIKI.md, LEARNING.md, AGENTS.md
  - .github/hooks/memory.json to wire SessionStart + Stop hooks

Safe to re-run — existing files are NOT overwritten.
"""

import json
import os
import sys

REPO_ROOT = os.getcwd()
PROJECT_MEMORY_DIR = os.path.join(REPO_ROOT, "project-memory")
HOOKS_DIR = os.path.join(REPO_ROOT, ".github", "hooks")
TEMPLATE_DIR = os.path.join(
    REPO_ROOT, ".github", "skills", "project-memory", "scripts", "templates"
)

MEMORY_FILES = [
    ("MEMORY.md", "MEMORY.md"),
    ("WIKI.md", "WIKI.md"),
    ("LEARNING.md", "LEARNING.md"),
    ("AGENTS.md", "AGENTS.md"),
]

HOOK_CONFIG = {
    "hooks": {
        "SessionStart": [
            {
                "type": "command",
                "command": "python .github\\skills\\project-memory\\scripts\\session_start.py",
                "timeout": 10
            }
        ],
        "Stop": [
            {
                "type": "command",
                "command": "python .github\\skills\\project-memory\\scripts\\indexer.py",
                "timeout": 15
            }
        ]
    }
}


def get_template(template_name: str) -> str:
    """Read a template file from the templates directory."""
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"# {template_name.replace('.md', '')}\n\n_(Template not found. Please create this file manually.)_"


def create_memory_files() -> tuple:
    """Create the 4 project-memory files from templates."""
    os.makedirs(PROJECT_MEMORY_DIR, exist_ok=True)
    created = 0
    skipped = 0

    for filename, template_name in MEMORY_FILES:
        filepath = os.path.join(PROJECT_MEMORY_DIR, filename)
        if os.path.exists(filepath):
            print(f"  ⏩ project-memory/{filename} — already exists, skipped")
            skipped += 1
            continue

        content = get_template(template_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ project-memory/{filename} — created")
        created += 1

    return created, skipped


def create_hook_config() -> tuple:
    """Create .github/hooks/memory.json to wire SessionStart and Stop hooks."""
    os.makedirs(HOOKS_DIR, exist_ok=True)
    hook_path = os.path.join(HOOKS_DIR, "memory.json")

    if os.path.exists(hook_path):
        print(f"  ⏩ .github/hooks/memory.json — already exists, skipped")
        return 0, 1

    with open(hook_path, "w", encoding="utf-8") as f:
        json.dump(HOOK_CONFIG, f, indent=2)
    print(f"  ✅ .github/hooks/memory.json — created")
    return 1, 0


def main():
    print("🚀 Initializing Project Memory System...\n")

    print("📁 Memory files:")
    mem_created, mem_skipped = create_memory_files()

    print("\n🔗 Hook configuration:")
    hook_created, hook_skipped = create_hook_config()

    total_created = mem_created + hook_created
    total = len(MEMORY_FILES) + 1

    print(f"\nDone: {total_created} created, {mem_skipped + hook_skipped} skipped (of {total})")

    if total_created > 0:
        print("\n📋 Next steps:")
        print("   1. Review project-memory/AGENTS.md and merge its rules into your root AGENTS.md or .github/copilot-instructions.md")
        print("   2. The hooks in .github/hooks/memory.json will auto-load MEMORY.md at session start")
        print("      and rebuild the knowledge index at session end.")
    else:
        print("\n✅ Everything is already set up.")

    sys.exit(0)


if __name__ == "__main__":
    main()
