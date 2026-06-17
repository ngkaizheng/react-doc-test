# Phase 3: MCP Server

## Goal
Replace the CLI retriever and FastAPI server with a native MCP server that VS Code manages directly. The agent calls tools via MCP protocol instead of shell commands.

## Architecture

```
VS Code Copilot Agent
          |
          | MCP Protocol (stdio)
          |
          v
project-memory MCP Server (mcp-server.py)
          |
          ├── embedding model (warm at startup)
          ├── Chroma vector DB
          ├── MEMORY.md
          ├── docs/WIKI.md
          ├── docs/LEARNING.md
          └── docs/features/*.md
```

## Tools

| Tool | What it does | Replaces |
|------|-------------|----------|
| `search_memory` | Semantic search over all docs | `retriever.py --query` |
| `get_memory` | Read current MEMORY.md | `read_file MEMORY.md` |
| `update_current_task` | Update Current Task section | Manual edit |
| `append_memory_note` | Add note to MEMORY.md | Manual edit |
| `clear_completed_tasks` | Clear completed items | Manual edit |
| `add_learning` | Append to LEARNING.md | Manual edit |
| `add_wiki_entry` | Append to WIKI.md | Manual edit |
| `index_status` | Chroma collection stats | `retriever-server.py /stats` |
| `refresh_index` | Re-run indexer to sync Chroma | `python indexer.py` |

## Resources

| Resource | Content |
|----------|---------|
| `memory://current` | Current MEMORY.md content |
| `memory://index-status` | Index statistics |

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SDK | `mcp[cli]` with FastMCP | Standard, typed tools |
| Transport | stdio | VS Code manages lifecycle, no ports |
| Model loading | At startup, kept warm | Same as Phase 2 server |
| Granular tools | Yes (not raw `update_memory`) | Prevents accidental overwrites |
| `refresh_index` | Calls indexer internally | Keeps Chroma in sync after writes |

## Files to Create/Modify

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `scripts/memory.py` | **NEW** | File operations for MEMORY/WIKI/LEARNING |
| 2 | `scripts/mcp-server.py` | **NEW** | FastMCP server with tools + resources |
| 3 | `.vscode/mcp.json` | **NEW** | VS Code MCP server configuration |
| 4 | `templates/AGENTS.md` | **MODIFY** | Document MCP tools usage |
| 5 | `SKILL.md` | **MODIFY** | Document MCP server + tools |
| 6 | `scripts/init.py` | **MODIFY** | Generate .vscode/mcp.json |

## Dependencies Added

```bash
pip install mcp[cli]
```
Replaces `fastapi` + `uvicorn` from Phase 2 (single dependency instead of two).

## Evolution Path

```
Phase 1: python retriever.py --query "..."    (CLI, loads model each time)
Phase 2: retriever-server.py + --server flag  (FastAPI, warm model)
Phase 3: MCP server                           (native protocol, no shell)
```

After Phase 3, the Phase 2 FastAPI server can be deprecated.
