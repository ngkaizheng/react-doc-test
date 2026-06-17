# Agent Rules — Project Memory (Vector DB Edition)

## 🔴 Retrieval Priority Rule

When you need project knowledge:

1. **FIRST** → `search_memory(query, top_k=5, threshold=0.3, format="m2m")`
2. **SECOND** → If no useful results, `grep_search` / `file_search` as fallback.

## MCP Tools

| Tool | Params |
|------|--------|
| `search_memory(query, top_k, threshold, format)` | `format="m2m"` (default, lean) or `"json"` (explicit). Returns `ID`/`SCORE`/`SRC`/`PATH`/`LINES`/`TEXT` blocks |
| `get_memory()` | Reads MEMORY.md sections: `## [CT]`, `## [NS]`, `## [BL]`, `## [CM]` |
| `update_working_memory(current_task, next_steps, blocked, append_note, clear_completed)` | Updates bracketed sections by name — empty param = skip |
| `add_learning(title, problem, root_cause, solution, key_takeaway)` | Appends new lesson to LEARNING.md top |
| `add_wiki_entry(heading, content, section)` | Adds `###` under `## section` (skips duplicate) |
| `update_wiki_entry(heading, content, section)` | Replaces existing `###` content |
| `expand_wiki_entry(heading, content, section)` | Appends to existing `###` |
| `remove_wiki_entry(heading, section)` | Deletes `###` block |
| `refresh_index()` | Rebuild vector index after doc changes |
| `index_status()` | Check index health |

## Context Retrieval

1. **MEMORY.md loaded at session start.** Read it. Sections: `[CT]`, `[NS]`, `[BL]`, `[CM]`.
2. **Do NOT read docs/ files in full.** Use `search_memory()`.
3. After results: use `read_file` with `LINES` range (e.g., `LINES: 17-19` → lines 17-19).
4. Use `PATH` breadcrumb (e.g., `PATH: Tech Stack > Vercel`) for architectural context.
5. Read docs/ when: user asks about architecture/decisions, reports a bug, or before making a design decision.
6. Update MEMORY.md via `update_working_memory()` as progress changes.

## Heading Level Standards

| File | `##` = | `###` = |
|------|--------|---------|
| **WIKI.md** | Major domain | Sub-topic or decision entry |
| **LEARNING.md** | Distinct lesson | Update to existing lesson |
| **features/*.md** | Major component | Sub-component or edge case |

## Write Standards

### LEARNING.md
1. `search_memory(keywords)` — check for existing similar lesson.
2. **Same issue?** → Expand existing `##` via `add_learning()` (appends `### Update`).
3. **New?** → `add_learning()` at top. Format: `**Problem:**` / `**Root Cause:**` / `**Solution:**` / `**Key Takeaway:**`.

### WIKI.md
- Fits under existing `##`? → `add_wiki_entry()` with `section=` param.
- No match? → `add_wiki_entry()` without section (creates new `##`).
- Key Decisions: new `### YYYY-MM-DD: Title` at top of `## Key Decisions`.

### MEMORY.md
- Rewrite `## [CT]` and `## [NS]` as priorities shift.
- Mark `[ ]` → `[x]` when done.
- Never delete completed items until user agrees to wipe for a new feature.

## Subagent Protocol

When spawning any subagent:
1. Include relevant context from MEMORY.md in your prompt to the subagent.
2. If the subagent needs project knowledge, run retriever.py yourself and include the results.
3. Demand structured output: "Return your findings with: [completed], [discoveries], [blockers], [output]."
4. After the subagent returns, capture any learnings into LEARNING.md and update MEMORY.md.

## Session End

- If all tasks in MEMORY.md are complete, ask: "All tasks in MEMORY.md are complete. Should I archive this content to WIKI.md and clear MEMORY.md for the next feature?"
- Otherwise, ensure MEMORY.md reflects current state for next session.
