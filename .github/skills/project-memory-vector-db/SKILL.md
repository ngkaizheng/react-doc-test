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

This skill gives you **semantic retrieval** over the project's documentation (`docs/WIKI.md`, `docs/LEARNING.md`, `docs/features/*.md`) and **working memory** (`MEMORY.md`) via MCP tools.

## 🔴 MANDATORY: Always Use MCP Tools First

**Never** read documentation files directly. Always use the MCP tools below.

When you need project knowledge (architecture, design, features, bugs, standards, decisions):

1. **FIRST** → Call `search_memory(query)` — semantic search finds conceptually related content even when keywords don't match.
2. **SECOND** → If search returns nothing useful, use `grep_search` or `file_search` as fallback.
3. **Always read from results** → Use `read_file` with the `line_start`/`line_end` from search results to get full context.

## MCP Tools

| Tool | When to call |
|------|-------------|
| `search_memory(query, top_k, threshold)` | Any knowledge question — this is your primary retrieval tool |
| `get_memory()` | Session start: read MEMORY.md for current task context |
| `update_current_task(task)` | When you start/pivot on a task — keeps MEMORY.md current |
| `append_memory_note(note)` | Record a discovery, blocker, or decision mid-session |
| `clear_completed_tasks()` | When user agrees to clear MEMORY.md for a new feature |
| `add_learning(title, problem, root_cause, solution, key_takeaway)` | When you discover a reusable lesson |
| `add_wiki_entry(heading, content, section)` | When you need to record architecture, decisions, or standards |
| `refresh_index()` | After adding/modifying docs — rebuilds the vector index |
| `index_status()` | Check if the vector index is healthy and up to date |

## Workflows

### Answer a knowledge question
1. `search_memory("<the question>")` — let semantic search find relevant docs
2. `read_file` the matching sections using returned `line_start`/`line_end`
3. Answer the user with citations

### Add a lesson to LEARNING.md
1. `search_memory("<keywords>")` — check if similar knowledge exists
2. **Exact same issue?** → `add_learning()` with title `YYYY-MM-DD: ...`
   The tool appends as `### YYYY-MM-DD Update:` under existing sections automatically.
3. **New issue?** → `add_learning()` — creates new `## YYYY-MM-DD: Title` at top.

### Add wiki content
1. `add_wiki_entry(heading="Title", content="...", section="SectionName")`
2. Fits under existing `##`? Appends to that section. No match? Creates new `##` at bottom.

### Update working memory
1. `update_current_task("Implementing feature X")` — rewrite current task
2. `append_memory_note("Discovered that...")` — record mid-session findings
3. When task complete, mark in MEMORY.md via `append_memory_note`

### After editing documentation files
1. `refresh_index()` — rebuilds the Chroma vector index so new content is searchable
2. `index_status()` — verify the index is healthy

## Heading Level Standards

Both `##` and `###` are chunk boundaries in the vector index:

| File | `##` = | `###` = |
|------|--------|---------|
| **WIKI.md** | Major domain | Sub-topic or decision entry |
| **LEARNING.md** | Distinct lesson | Update to existing lesson |
| **features/*.md** | Major component | Sub-component or edge case |

## See Also

- [README.md](README.md) — Setup, installation, architecture, CLI/server usage, and script reference.
