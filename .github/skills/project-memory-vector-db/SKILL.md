---
name: project-memory-vector-db
description: >-
  Manages project long-term memory with semantic vector search over WIKI.md, LEARNING.md, and feature docs,
  plus working memory via MEMORY.md.
  Provides nine MCP tools (search_memory, get_memory, update_current_task, append_memory_note,
  clear_completed_tasks, add_learning, add_wiki_entry, refresh_index, index_status) for knowledge retrieval
  and documentation management.
  Use when the user asks about project knowledge, architecture, design decisions, standards, bugs, past
  features, or implementation guidance. Also triggers on: how does, how should, what is, implement,
  currently working on, add to wiki, save lesson, record decision, project memory, RAG, vector search.
  Does NOT handle code generation or debugging unrelated to project knowledge.
---

# Project Memory — Vector DB

Semantic retrieval over `docs/WIKI.md`, `docs/LEARNING.md`, `docs/features/*.md` + working memory via MCP tools.

## 🔴 Always Use MCP Tools First

**Never** read docs/ files directly. Always use MCP tools.

1. `search_memory(query, top_k=5, threshold=0.3, format="m2m")` — primary retrieval.
2. If empty → `grep_search` / `file_search` fallback.
3. Read results via `read_file` using `LINES` range from search output.

## MCP Tools

| Tool | Notes |
|------|-------|
| `search_memory(query, top_k, threshold, format)` | Default `format="m2m"`. Returns `ID`/`SCORE`/`SRC`/`PATH`/`LINES`/`TEXT` blocks separated by `---`. |
| `get_memory()` | Read MEMORY.md (sections: `## [CT]`, `## [NS]`, `## [BL]`, `## [CM]`) |
| `update_working_memory(current_task, next_steps, blocked, append_note, clear_completed)` | Updates bracketed sections by name |
| `add_learning(title, problem, root_cause, solution, key_takeaway)` | Appends to LEARNING.md top |
| `add_wiki_entry(heading, content, section)` | Adds `###` under `## section` |
| `update_wiki_entry(heading, content, section)` | Replaces `###` content |
| `expand_wiki_entry(heading, content, section)` | Appends to existing `###` |
| `remove_wiki_entry(heading, section)` | Deletes `###` block |
| `refresh_index()` | Rebuild vector index after doc changes |
| `index_status()` | Check index health |

## Workflows

### Answer question
1. `search_memory("<question>")`
2. `read_file(src_path, ls, le)` using `SRC:` and `LINES:` from results
3. Use `PATH:` breadcrumb (e.g., `Tech Stack > Vercel`) for hierarchy context
4. Answer with citations

### Add learning
1. `search_memory(keywords)` — check for duplicates
2. Same issue → `add_learning()` (appends `### Update` under existing)
3. New → `add_learning()` creates `## YYYY-MM-DD: Title` at top

### Add wiki content
1. `add_wiki_entry(heading="Title", content="...", section="Section")`
2. Fits under `## section`? Appends. No match? Creates new `##`.

### Update working memory
- `update_working_memory(current_task="...", next_steps="...", blocked="...")`
- Sections: `## [CT]`, `## [NS]`, `## [BL]`, `## [CM]`

### After editing docs
1. `refresh_index()`
2. `index_status()` — confirm healthy

## Heading Level Standards

Both `##` and `###` are chunk boundaries in the vector index:

| File | `##` = | `###` = |
|------|--------|---------|
| **WIKI.md** | Major domain | Sub-topic or decision entry |
| **LEARNING.md** | Distinct lesson | Update to existing lesson |
| **features/*.md** | Major component | Sub-component or edge case |

## See Also

- [README.md](README.md) — Setup, scripts, architecture.
