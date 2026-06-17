# Agent Rules — Project Memory (Vector DB Edition)

## 🔴 Retrieval Priority

1. `search_memory(query, top_k=5, threshold=0.3, format="m2m")` — primary.
2. If empty → `grep_search` / `file_search` fallback.

## MCP Tools

| Tool | Notes |
|------|-------|
| `search_memory(query, top_k, threshold, format)` | Default `format="m2m"`. Returns `ID`/`SCORE`/`SRC`/`PATH`/`LINES`/`TEXT` blocks. |
| `get_memory()` | MEMORY.md: sections `## [CT]`, `## [NS]`, `## [BL]`, `## [CM]` |
| `update_working_memory(current_task, next_steps, blocked, append_note, clear_completed)` | By-name updates |
| `add_learning(title, problem, root_cause, solution, key_takeaway)` | New lesson at top |
| `add_wiki_entry(heading, content, section)` | `###` under `## section` |
| `update_wiki_entry(heading, content, section)` | Replace `###` content |
| `expand_wiki_entry(heading, content, section)` | Append to `###` |
| `remove_wiki_entry(heading, section)` | Delete `###` |
| `refresh_index()` | Rebuild after doc changes |
| `index_status()` | Health check |

## Context Retrieval

1. MEMORY.md loaded at session start. Read it. Sections: `[CT]`, `[NS]`, `[BL]`, `[CM]`.
2. Do NOT read docs/ files in full. Use `search_memory()`.
3. Use `read_file` with `LINES:` range from results (e.g., `LINES: 17-19`).
4. Use `PATH:` breadcrumb (e.g., `Tech Stack > Vercel`) for hierarchy context.
5. Read docs/ when: user asks about architecture/decisions, reports a bug, or before a design decision.
6. Update MEMORY.md via `update_working_memory()`.

## Heading Level Standards

| File | `##` = | `###` = |
|------|--------|---------|
| **WIKI.md** | Major domain | Sub-topic / decision |
| **LEARNING.md** | Distinct lesson | Update to lesson |
| **features/*.md** | Major component | Sub-component / edge case |

## Write Standards

### LEARNING.md
1. `search_memory(keywords)` — check for existing lesson.
2. Same issue → `add_learning()` (appends `### Update` under existing).
3. New → `add_learning()` at top. Format: `**Problem:**` / `**Root Cause:**` / `**Solution:**` / `**Key Takeaway:**`.

### WIKI.md
- Fits under `##`? → `add_wiki_entry()` with `section=`.
- No match? → `add_wiki_entry()` without section (creates new `##`).
- Key Decisions: new `### YYYY-MM-DD: Title` at top of `## Key Decisions`.
- Never rewrite/delete without approval.

### MEMORY.md
- Rewrite `## [CT]`, `## [NS]` as priorities shift.
- Mark `[ ]` → `[x]`.
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
