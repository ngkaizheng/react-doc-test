"""
Initialization script for Project Memory Vector DB system.

Creates:
  - project-memory-vector-db/MEMORY.md
  - project-memory-vector-db/docs/WIKI.md, LEARNING.md
  - project-memory-vector-db/docs/features/ directory
  - project-memory-vector-db/manifest.json
  - .github/hooks/memory.json (wires SessionStart + Stop hooks)
  - Adds project-memory MCP server to .vscode/mcp.json

Safe to re-run — existing files are NOT overwritten.
"""

import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../.."
    )
)
PROJECT_DIR = os.path.join(REPO_ROOT, "project-memory-vector-db")
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
FEATURES_DIR = os.path.join(DOCS_DIR, "features")
HOOKS_DIR = os.path.join(REPO_ROOT, ".github", "hooks")
VSCODE_DIR = os.path.join(REPO_ROOT, ".vscode")
TEMPLATE_DIR = os.path.join(
    REPO_ROOT, ".github", "skills", "project-memory-vector-db", "scripts", "templates"
)

MCP_SERVER_ENTRY = {
    "type": "stdio",
    "command": "python",
    "args": [
        "${workspaceFolder}/.github/skills/project-memory-vector-db/scripts/mcp-server.py"
    ]
}

MEMORY_FILES = [
    ("MEMORY.md", "MEMORY.md"),
]

DOCS_FILES = [
    ("WIKI.md", "WIKI.md"),
    ("LEARNING.md", "LEARNING.md"),
]

HOOK_CONFIG = {
    "hooks": {
        "SessionStart": [
            {
                "type": "command",
                "command": "python .github\\skills\\project-memory-vector-db\\scripts\\session_start.py",
                "timeout": 10
            }
        ],
        "Stop": [
            {
                "type": "command",
                "command": "python .github\\skills\\project-memory-vector-db\\scripts\\indexer.py",
                "timeout": 30
            }
        ]
    }
}


def get_template(template_name: str) -> str:
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"# {template_name.replace('.md', '')}\n\n_(Template not found. Please create this file manually.)_"


def create_file_with_template(dir_path: str, filename: str, template_name: str) -> bool:
    """Create a single file from template. Returns True if created, False if skipped."""
    filepath = os.path.join(dir_path, filename)
    if os.path.exists(filepath):
        print(f"  ⏩ {os.path.basename(dir_path)}/{filename} — already exists, skipped")
        return False

    content = get_template(template_name)
    os.makedirs(dir_path, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ {os.path.basename(dir_path)}/{filename} — created")
    return True


def create_manifest() -> bool:
    """Create initial manifest.json if it doesn't exist."""
    manifest_path = os.path.join(PROJECT_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        print(f"  ⏩ manifest.json — already exists, skipped")
        return False

    manifest = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "files": {}
    }
    os.makedirs(PROJECT_DIR, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  ✅ manifest.json — created")
    return True


def create_hook_config() -> bool:
    hook_path = os.path.join(HOOKS_DIR, "memory.json")
    if os.path.exists(hook_path):
        print(f"  ⏩ .github/hooks/memory.json — already exists, skipped")
        return False

    os.makedirs(HOOKS_DIR, exist_ok=True)
    with open(hook_path, "w", encoding="utf-8") as f:
        json.dump(HOOK_CONFIG, f, indent=2)
    print(f"  ✅ .github/hooks/memory.json — created")
    return True


def create_mcp_config() -> bool:
    """Add project-memory MCP server to .vscode/mcp.json."""
    mcp_path = os.path.join(VSCODE_DIR, "mcp.json")
    os.makedirs(VSCODE_DIR, exist_ok=True)

    config = {"servers": {}}
    if os.path.exists(mcp_path):
        with open(mcp_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if "servers" not in config:
            config["servers"] = {}
        if "project-memory" in config["servers"]:
            print(f"  ⏩ .vscode/mcp.json — 'project-memory' server already registered")
            return False

    config["servers"]["project-memory"] = MCP_SERVER_ENTRY

    with open(mcp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"  ✅ .vscode/mcp.json — added 'project-memory' MCP server")
    return True


def main():
    print("🚀 Initializing Project Memory Vector DB System...\n")

    print("📁 Root files:")
    mem_created = 0
    for filename, template_name in MEMORY_FILES:
        if create_file_with_template(PROJECT_DIR, filename, template_name):
            mem_created += 1

    print("\n📄 Documentation files (docs/):")
    docs_created = 0
    for filename, template_name in DOCS_FILES:
        if create_file_with_template(DOCS_DIR, filename, template_name):
            docs_created += 1

    # Ensure features/ directory exists
    os.makedirs(FEATURES_DIR, exist_ok=True)
    print(f"\n📂 docs/features/ directory ready at: {FEATURES_DIR}")

    print("\n📋 Manifest:")
    manifest_created = create_manifest()

    print("\n🔗 Hook configuration:")
    hook_created = create_hook_config()

    print("\n🤖 MCP server configuration:")
    mcp_created = create_mcp_config()

    total_created = mem_created + docs_created + (1 if manifest_created else 0) + (1 if hook_created else 0) + (1 if mcp_created else 0)
    total = 2 + 2 + 1 + 1 + 1  # memory files + docs files + manifest + hook + mcp

    print(f"\nDone: {total_created} created, {total - total_created} skipped (of {total})")

    if total_created > 0:
        print("\n📋 Next steps:")
        print("   1. Install dependencies: pip install chromadb sentence-transformers mcp[cli]")
        print("   2. Review docs/AGENTS.md and merge rules into your root AGENTS.md")
        print("   3. Run the indexer to build the vector database:")
        print("      python .github/skills/project-memory-vector-db/scripts/indexer.py")
        print("   4. Restart VS Code to activate the MCP server (in .vscode/mcp.json)")
    else:
        print("\n✅ Everything is already set up.")


if __name__ == "__main__":
    main()
