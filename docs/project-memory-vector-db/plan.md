# Project Memory Vector DB — Implementation Plan

## Architecture

```
project-memory-vector-db/
├── MEMORY.md                    ← Loaded every session (working memory)
├── docs/                        ← Human source of truth
│   ├── WIKI.md                  ← Architecture, decisions, standards
│   ├── LEARNING.md              ← Lessons learned, bug fixes
│   └── features/                ← Feature documentation (any number of .md files)
│       ├── payment.md
│       ├── login.md
│       └── ...
├── vector-db/                   ← Chroma persistent storage (auto-managed, .gitignore)
├── manifest.json                ← Change tracking (file hash → last indexed)
└── .github/
    ├── hooks/
    │   └── memory.json          ← Wires SessionStart + Stop hooks
    └── skills/
        └── project-memory-vector-db/
            ├── SKILL.md
            └── scripts/
                ├── init.py           ← Bootstrap: creates docs/ + manifest.json
                ├── indexer.py        ← Stop hook: chunk → embed → store in Chroma
                ├── retriever.py      ← On-demand: query Chroma, return relevant chunks
                ├── session_start.py  ← SessionStart: load MEMORY.md, mention vector search
                └── templates/
                    ├── MEMORY.md
                    ├── WIKI.md
                    ├── LEARNING.md
                    └── AGENTS.md
```

## Data Flow

```
Write phase (Stop hook):
  docs/WIKI.md, LEARNING.md, features/*.md
    → indexer.py
      → chunk by H2/H3 headings
      → embed with sentence-transformers/all-MiniLM-L6-v2
      → store in Chroma (vector-db/)
      → update manifest.json (file hash tracking)

Read phase (on-demand, agent calls):
  agent needs knowledge
    → retriever.py --query "..." --top-k 5
      → embed query
      → search Chroma
      → return JSON: [{file, heading, line_start, line_end, score, preview}]
    → agent reads full section via read_file
```

## Chunking Strategy

Based on Microsoft RAG best practices for markdown:
- **Boundary:** H2 (`##`) and H3 (`###`) headings — format-specific chunking
- **Enrichment:** Each chunk carries metadata: source file, heading, line range, parent heading
- **No overlap needed:** Heading boundaries are natural semantic separators
- **Max chunk size:** Sections exceeding 512 tokens are further split by paragraph

## Vector Store Schema (Chroma)

```python
collection.add(
    ids=["payment-retry-001"],
    embeddings=[[0.123, -0.456, ...]],  # 384-dim from all-MiniLM-L6-v2
    metadatas=[{
        "file": "docs/features/payment.md",
        "heading": "Retry Logic",
        "parent_heading": "Payment Flow",
        "line_start": 40,
        "line_end": 70,
        "section_key": "retry-logic"
    }],
    documents=["Payment retry happens after failed transaction..."]
)
```

## Dependencies

```bash
pip install chromadb sentence-transformers
```

- `chromadb` — embedded vector DB (no server)
- `sentence-transformers` — local embedding model (all-MiniLM-L6-v2, 80MB, 384-dim)
- Total: ~150MB disk, one-time download on first run

## Implementation Steps

| # | Step | Files | Complexity |
|---|------|-------|------------|
| 1 | Update SKILL.md frontmatter + description | `SKILL.md` | Low |
| 2 | Rewrite indexer.py — chunk + embed + store | `scripts/indexer.py` | High |
| 3 | Create retriever.py — query Chroma | `scripts/retriever.py` | Medium |
| 4 | Update session_start.py — mention vector search | `scripts/session_start.py` | Low |
| 5 | Update init.py — new layout (docs/, manifest) | `scripts/init.py` | Medium |
| 6 | Update AGENTS.md template — vector instructions | `scripts/templates/AGENTS.md` | Medium |
| 7 | Update templates — WIKI.md, LEARNING.md | `scripts/templates/` | Low |
| 8 | Update hook config — point paths | `.github/hooks/memory.json` | Low |
| 9 | Verify scripts, test, commit | — | Low |

## Edge Cases Handled

- **First run:** Model downloads automatically, user sees progress
- **Changed files:** Manifest tracks SHA256 hashes — only re-indexes changed files
- **Deleted files:** Manifest detects missing files, removes from Chroma
- **Empty docs/:** Indexer handles gracefully, outputs warning
- **Very long sections:** Split by paragraph if >512 tokens
- **Chroma corruption:** Delete vector-db/ and re-run indexer = full rebuild

---

## Phase 2: Persistent Retrieval Server

### Problem
Every retriever.py call loads the 80MB embedding model → ~1-2s latency per query.

### Solution
FastAPI server (`retriever-server.py`) keeps the model warm in memory. Queries drop to ~50ms.

### Architecture
```
retriever-server.py (long-running process)
    │
    ├── Startup: load all-MiniLM-L6-v2 once
    ├── Connect to Chroma
    │
    └── Endpoints:
        GET /search?q=...&k=5     → JSON results (same format as CLI)
        GET /health                → {"status": "ok"}
        GET /stats                 → collection statistics
```

### Client Mode
`retriever.py --server` delegates to the server via HTTP instead of loading the model directly. Falls back to direct mode (model load per query) if `--server` is not specified.

### Dependencies (server only)
```bash
pip install fastapi uvicorn
```
~5MB additional, only needed if running the server.

### When to Use Server Mode
| Scenario | Use Direct | Use Server |
|----------|-----------|------------|
| Single query per session | ✅ Fine | ⚠️ Overkill |
| Multiple queries per session | ❌ 1-2s each | ✅ 50ms each |
| Many feature docs (100+) | ❌ Slow | ✅ Fast |
| Quick one-off lookup | ✅ Simple | ⚠️ Extra setup |
