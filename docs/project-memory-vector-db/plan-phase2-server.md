# Phase 2: Persistent Retrieval Server

## Goal
Eliminate model reload overhead (~1-2s per query) by keeping the embedding model warm in a local FastAPI server.

## Problem
```
Current (Phase 1):                     Phase 2 (Server):
query 1 → load model → search          startup → load model once
query 2 → load model → search          query 1 → 50ms search
query 3 → load model → search          query 2 → 50ms search
          ↑ 1-2s each                             ↑ no reload
```

## Architecture

```
VS Code Agent
     │
     ├── (one-time) start-server.ps1 → launches retriever-server.py
     │
     └── python retriever.py --server --query "..."
                              │
                              ▼
                    http://localhost:8000/search?q=...
                              │
                              ▼
                    retriever-server.py (model always loaded)
                              │
                              ▼
                    Chroma vector DB → JSON response
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | FastAPI + uvicorn | Standard, async, auto-docs at /docs |
| Port | 8000 (configurable via --port) | Avoids conflicts with common services |
| Binding | 127.0.0.1 only | Local-only, no network exposure |
| Model reuse | Same as retriever.py (all-MiniLM-L6-v2) | Consistency, no extra download |
| Output format | Identical to retriever.py CLI | Agent uses same parsing either way |
| Client mode | `--server` flag on retriever.py | Single entry point for the agent |

## Files to Create/Modify

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `scripts/retriever_lib.py` | **NEW** | Shared formatting logic (format_results, truncate_preview, paths) |
| 2 | `scripts/retriever-server.py` | **NEW** | FastAPI server with /search and /health endpoints |
| 3 | `scripts/retriever.py` | **MODIFY** | Add --server/--port flags; delegate to server when set |
| 4 | `scripts/start-server.ps1` | **NEW** | Windows launcher (starts uvicorn in background) |
| 5 | `templates/AGENTS.md` | **MODIFY** | Document server mode usage |
| 6 | `SKILL.md` | **MODIFY** | Document server component |
| 7 | `plan.md` | **MODIFY** | Add Phase 2 to architecture evolution |

## Dependencies Added

```bash
pip install fastapi uvicorn
```
~5MB additional. Only needed if running the server.

## Implementation Steps

| Step | What | Files |
|------|------|-------|
| 1 | Extract shared formatting into retriever_lib.py | `retriever_lib.py` (NEW), `retriever.py` (refactor) |
| 2 | Create FastAPI server | `retriever-server.py` (NEW) |
| 3 | Add --server mode to retriever.py | `retriever.py` |
| 4 | Create Windows launcher | `start-server.ps1` (NEW) |
| 5 | Update AGENTS.md | `templates/AGENTS.md` |
| 6 | Update SKILL.md | `SKILL.md` |
| 7 | Verify all scripts, commit | — |
