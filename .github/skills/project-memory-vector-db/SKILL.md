---
name: project-memory-vector-db
description: >-
  Manages project long-term memory with dynamic, configurable knowledge sources
  (knowledge-sources.json) and semantic vector search across any repo path,
  plus working memory via MEMORY.md.
  Provides MCP tools (search_memory, get_memory, update_working_memory, add_learning, add_wiki_entry,
  update_wiki_entry, expand_wiki_entry, remove_wiki_entry, refresh_index, index_status) for knowledge
  retrieval and documentation management.
  Use when the user asks about project knowledge, architecture, design decisions, standards, bugs, past
  features, or implementation guidance. Also triggers on: how does, how should, what is, implement,
  currently working on, add to wiki, save lesson, record decision, project memory, RAG, vector search.
  Does NOT handle code generation or debugging unrelated to project knowledge.
---

# Project Memory — Vector DB

Semantic retrieval + working memory.

## 🔴 Retrieval Priority

1. `search_memory(query, top_k=5, threshold=0.3, format="m2m")` — primary retrieval.
2. If empty → `grep_search` / `file_search` fallback.
3. `read_file` target using `SRC:` and `LINES:` from results.

## MCP Tools

| Tool | Contract |
|------|----------|
| `search_memory(query, top_k, threshold, format, source, keywords)` | `query`: natural language. `top_k`: 1-50 (default 5). `threshold`: 0.0-1.0 (default 0.3). `format`: `"m2m"` (default) or `"json"`. `source`: filter by source label (e.g., `"Core Knowledge"`). `keywords`: hybrid boost — exact matches rank higher. Returns `ID`/`SCORE`/`SRC`/`SOURCE`/`PATH`/`LINES`/`TEXT` blocks. |
| `memory_stats()` | Returns per-source chunk/file counts, embedding model, last indexed. Use to check what knowledge is available. |
| `get_memory()` | Reads MEMORY.md. Sections: `## [CT]`, `## [NS]`, `## [BL]`, `## [CM]`. |
| `update_working_memory(current_task, next_steps, blocked, append_note, clear_completed)` | Each param maps to a named section. Empty = skip. |
| `add_learning(title, problem, root_cause, solution, key_takeaway)` | Appends to LEARNING.md top. |
| `add_wiki_entry(heading, content, section)` | Adds `### heading` under `## section`. Skips if duplicate. `section` optional — creates new `##` if omitted. |
| `update_wiki_entry(heading, content, section)` | Replaces existing `### heading`. `section` required. |
| `expand_wiki_entry(heading, content, section)` | Appends to existing `### heading`. `section` required. |
| `remove_wiki_entry(heading, section)` | Removes entire `### heading` block. `section` required. |
| `refresh_index()` | Rebuilds Chroma vector index. |
| `index_status()` | Returns chunk count and health. |

## Workflows

### Answer question
1. `search_memory("<question>")` — find relevant docs
2. `read_file` target using `SRC:` and `LINES:` from results
3. Use `PATH:` breadcrumb (e.g., `Tech Stack > Vercel`) for hierarchy context
4. Answer with citations

**💡 Pro tips for better search:**
- **Narrow by source**: `search_memory("auth", source="Specifications")` — only searches within a specific knowledge source
- **Keyword boost**: `search_memory("RLS policy", keywords="row_level_security")` — exact term matches rank higher
- **Check what's indexed**: `memory_stats()` — shows per-source chunk counts so you know what's searchable
- **Too few results?** Lower threshold: `search_memory("...", threshold=0.15)`

### Add lesson
1. `search_memory(keywords)` — check for duplicates
2. **Same issue?** → `add_learning()` with title `YYYY-MM-DD: ...` (appends `### Update` under existing)
3. **New issue?** → `add_learning()` — creates new `## YYYY-MM-DD: Title` at top

### Add wiki content
1. `add_wiki_entry(heading="Title", content="...", section="SectionName")`
2. Fits under `##`? Appends. No match? Creates new `##` at bottom.

### Update working memory
- `update_working_memory(current_task="...", next_steps="...", blocked="...")`
- Sections: `## [CT]`, `## [NS]`, `## [BL]`, `## [CM]`

### After editing docs or knowledge sources
1. `refresh_index()` — rebuild Chroma vector index (reads `knowledge-sources.json` dynamically)
2. `index_status()` — verify index health

## Heading Level Standards

Both `##` and `###` are chunk boundaries in the vector index (applies to all indexed .md files):

| File type | `##` = | `###` = |
|-----------|--------|---------|
| **WIKI.md / general docs** | Major domain | Sub-topic or decision entry |
| **LEARNING.md** | Distinct lesson | Update to existing lesson |
| **features/*.md / specs** | Major component | Sub-component or edge case |

## See Also

- [README.md](README.md) — Setup, scripts, architecture.
