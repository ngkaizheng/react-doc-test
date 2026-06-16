---
name: project-memory-vector-db
description: >-
  Manage the project's long-term memory using vector search over WIKI.md, LEARNING.md, and feature docs.
  Provides hooks-based context injection at session start, automatic Chroma vector indexing at session end,
  and on-demand semantic retrieval via MCP tools (search_memory, add_learning, etc.).
  Run `init.py` to bootstrap the files in a new repo.
  Triggers on: project memory, session context, knowledge management, long-term memory,
  RAG, vector search, semantic search, MCP, feature docs, wiki, lessons learned, agent rules,
  architecture, design, implement, how does, how should, what is, project knowledge,
  codebase knowledge, feature documentation, coding standards, tech stack.
---

# Project Memory Skill — Vector DB Edition

This skill implements a **semantic retrieval (RAG) system** for AI agents. It uses **Chroma** (embedded vector database) and **sentence-transformers** to index your project knowledge by meaning, not just keywords. The agent retrieves only the most relevant chunks on-demand, minimizing token waste.

## File Structure

```
repo-root/
├── project-memory-vector-db/
│   ├── MEMORY.md              ← Loaded every session (working memory)
│   ├── docs/                  ← Human source of truth (markdown files)
│   │   ├── WIKI.md            ← Architecture, decisions, standards
│   │   ├── LEARNING.md        ← Lessons learned, bug fixes
│   │   └── features/          ← Feature documentation (add any .md files)
│   │       ├── payment.md
│   │       └── login.md
│   ├── vector-db/             ← Chroma persistent storage (auto-managed)
│   └── manifest.json          ← Change tracking (file hashes)
├── .github/
│   ├── hooks/
│   │   └── memory.json        ← Wires SessionStart + Stop hooks
│   └── skills/
│       └── project-memory-vector-db/
│           ├── SKILL.md
│           ├── plan.md
│           ├── plan-phase2-server.md
│           └── scripts/
│               ├── init.py              ← Bootstrap docs/ + manifest.json
│               ├── session_start.py     ← Reads MEMORY.md → systemMessage
│               ├── indexer.py           ← Stop hook: chunk → embed → store in Chroma
│               ├── retriever.py         ← On-demand: semantic search (CLI or server mode)
│               ├── retriever_lib.py     ← Shared formatting utilities
│               ├── retriever-server.py  ← FastAPI server (keeps model warm)
│               ├── mcp-server.py        ← MCP server (native tools for VS Code agent)
│               ├── memory.py            ← File operations for MEMORY/WIKI/LEARNING
│               ├── start-server.ps1     ← Windows launcher for server
│               └── templates/
│                   ├── MEMORY.md
│                   ├── WIKI.md
│                   ├── LEARNING.md
│                   └── AGENTS.md
```

## How It Works

### Session Start
A `SessionStart` hook reads `MEMORY.md` and injects it as the agent's system message,
telling the agent which MCP tools are available and the retrieval priority rule.

### Knowledge Retrieval
The agent uses MCP tools (primarily `search_memory`) to find relevant knowledge.
Results include file paths and line numbers so the agent can `read_file` the
full section. A CLI fallback (`retriever.py`) is available if MCP is unavailable.

### Indexing
A `Stop` hook runs `indexer.py` at session end. It scans all markdown files in
`docs/`, chunks by H2/H3 headings, embeds via `all-MiniLM-L6-v2`, and stores
in Chroma. Only changed files are re-indexed (SHA256 change tracking).

## MCP Server

The skill includes a native **MCP server** (`mcp-server.py`) that the VS Code agent can call directly — no shell commands needed.

### Configuration
The MCP server is registered in `.vscode/mcp.json`:
```json
{
  "servers": {
    "project-memory": {
      "type": "stdio",
      "command": "python",
      "args": ["${workspaceFolder}/.github/skills/project-memory-vector-db/scripts/mcp-server.py"]
    }
  }
}
```
VS Code automatically starts the server on demand and keeps it running for the session.

### Tools

| Tool | Description |
|------|-------------|
| `search_memory(query, top_k, threshold)` | Semantic search over all documentation |
| `get_memory()` | Read current MEMORY.md |
| `update_current_task(task)` | Update Current Task section |
| `append_memory_note(note)` | Add a note to MEMORY.md |
| `clear_completed_tasks()` | Clear Completed section |
| `add_learning(title, problem, ...)` | Add lesson to LEARNING.md |
| `add_wiki_entry(heading, content, section)` | Add entry to WIKI.md |
| `refresh_index()` | Rebuild Chroma index after doc changes |
| `index_status()` | Check vector DB health |

### Resources
| Resource | Content |
|----------|---------|
| `memory://current` | Current MEMORY.md |
| `memory://index-status` | Index statistics |

## Dependencies

```bash
pip install chromadb sentence-transformers mcp[cli]
```

- **chromadb** — embedded vector database (no server, on-disk storage)
- **sentence-transformers** — local embedding model (`all-MiniLM-L6-v2`, 80MB, 384-dim)
- **mcp[cli]** — MCP Python SDK for native VS Code agent tools
- Total disk: ~155MB (one-time download on first run)

## Getting Started in a New Repo

```bash
# From the repo root:
python .github/skills/project-memory-vector-db/scripts/init.py
```

Then merge or copy the AGENTS.md rules into your root AGENTS.md or .github/copilot-instructions.md.

## Maintenance

### MEMORY.md
Agent updates in-place during sessions — rewrites `## Current Task`, checks off items. When complete, agent asks to archive to WIKI.md and clear for next feature.

### WIKI.md — "Grow Sections, Don't Split Them"
Append-and-grow only. New info adds to existing `##` sections or creates new `##` at bottom. `###` sub-topics for distinct sub-topics. `## Key Decisions` entries at top.

### LEARNING.md — "Check First, Then Write"
Reverse-chronological at top. Before writing, agent runs retriever.py to check if similar knowledge exists:
- **Exact same issue?** → Appends as `### YYYY-MM-DD Update:` under existing section.
- **New issue?** → New `## YYYY-MM-DD: Title` at top.

### manifest.json
Tracks SHA256 hashes of all indexed files. Auto-updated by indexer.py. No manual editing needed.

### vector-db/
Chroma persistent storage. Auto-managed. Add to `.gitignore`. Delete and re-run indexer to rebuild.

## Scripts Reference

| Script | When to Run | What It Does |
|--------|-------------|-------------|
| `init.py` | New repo setup | Creates docs/ + templates + manifest.json |
| `session_start.py` | Automatically (SessionStart hook) | Reads MEMORY.md → outputs systemMessage |
| `indexer.py` | Automatically (Stop hook) | Chunks docs → embeds → stores in Chroma |
| `retriever.py` | On-demand by agent | Semantic search (CLI fallback) |
| `mcp-server.py` | Auto by VS Code (MCP) | Native tools: search, read, write memory files |
| `memory.py` | Imported by mcp-server.py | File operations for MEMORY/WIKI/LEARNING |
| `retriever-server.py` | Manual (persistent process) | FastAPI server, keeps model warm in memory |
| `start-server.ps1` | Manual (Windows) | Launches retriever-server.py in background |
| `retriever_lib.py` | Imported by other scripts | Shared formatting utilities |
