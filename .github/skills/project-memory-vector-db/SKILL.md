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

### Index Phase (Stop Hook)
The `indexer.py` script runs automatically at the end of every agent session. It:
1. Reads `docs/WIKI.md`, `docs/LEARNING.md`, and all `docs/features/*.md`
2. Splits each file into chunks by H2 (`##`) and H3 (`###`) headings
3. Generates embeddings using **sentence-transformers/all-MiniLM-L6-v2** (384-dim)
4. Stores chunks in **Chroma** (persistent, on-disk) with metadata (file, heading, line range)
5. Updates `manifest.json` with file hashes to track changes

Only changed files are re-indexed — incremental by default.

### Retrieval Phase (On-Demand)
When the agent needs knowledge, it runs the retriever in one of two modes:

**Direct mode (default) — loads model per query (~1-2s):**
```bash
python .github/skills/project-memory-vector-db/scripts/retriever.py --query "..." --top-k 5
```

**Server mode — connects to persistent server (~50ms):**
```bash
# Terminal 1: Start the server once
pip install fastapi uvicorn
python .github/skills/project-memory-vector-db/scripts/retriever-server.py --port 8000

# Terminal 2 (or agent): Query via server
python .github/skills/project-memory-vector-db/scripts/retriever.py --server --query "..." --top-k 5
```

The retriever:
1. Embeds the query using the same `all-MiniLM-L6-v2` model
2. Searches Chroma for the most similar chunks
3. Returns JSON: file path, heading, line range, similarity score, content preview
4. The agent reads the full section using `read_file`

### Session Start (SessionStart Hook)
The `session_start.py` script runs at session start and:
1. Reads `MEMORY.md` — injects as `systemMessage`
2. Informs the agent: "Vector search is available via MCP tools or retriever.py"

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

### Dependency
```bash
pip install mcp[cli]
```

### Evolution
The MCP server is Phase 3 of the project memory evolution:
- **Phase 1:** `retriever.py` CLI (loads model per query)
- **Phase 2:** `retriever-server.py` FastAPI (warm model, HTTP)
- **Phase 3:** `mcp-server.py` MCP (native protocol, no shell)

## Dependencies

```bash
pip install chromadb sentence-transformers
```

- **chromadb** — embedded vector database (no server, on-disk storage)
- **sentence-transformers** — local embedding model (`all-MiniLM-L6-v2`, 80MB, 384-dim)
- Total disk: ~150MB (one-time download on first run)

## Getting Started in a New Repo

```bash
# From the repo root:
python .github/skills/project-memory-vector-db/scripts/init.py
```

Then merge or copy the AGENTS.md rules into your root AGENTS.md or .github/copilot-instructions.md.

## Chunking Strategy

Based on Microsoft RAG best practices for markdown (format-specific chunking):
| Aspect | Approach |
|--------|----------|
| **Boundary** | H2 (`##`) and H3 (`###`) headings |
| **Overlap** | None needed — headings are natural semantic separators |
| **Max size** | Sections exceeding 512 tokens are split by paragraph |
| **Metadata** | Source file, heading, parent heading, line_start, line_end, section_key |
| **Model** | `all-MiniLM-L6-v2` — 384-dim, good balance of speed vs quality |

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
| `retriever.py` | On-demand by agent | Semantic search (direct or `--server` mode) |
| `mcp-server.py` | Auto by VS Code (MCP) | Native tools: search, read, write memory files |
| `memory.py` | Imported by mcp-server.py | File operations for MEMORY/WIKI/LEARNING |
| `retriever-server.py` | Manual (persistent process) | FastAPI server, keeps model warm in memory |
| `start-server.ps1` | Manual (Windows) | Launches retriever-server.py in background |
| `retriever_lib.py` | Imported by other scripts | Shared formatting utilities |
