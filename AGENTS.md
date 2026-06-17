# Agent Rules — Project Memory (Vector DB Edition)

## 🔴 MANDATORY: Retrieval Priority Rule

When you need project knowledge (architecture, design, features, bugs, standards, decisions):

1. **FIRST** → Call `search_memory(query)` — this is a semantic/vector search that finds
   conceptually related content even when exact keywords don't match.
2. **SECOND** → If `search_memory()` returns no useful results, use `grep_search` or
   `file_search` as fallback.

**Why this order matters:** Vector search finds *meaning* not just *text*. A query like
"payment retry" will also match "transaction failure recovery" and "billing retry logic" —
things keyword search misses entirely.

## MCP Tools Available

This project has an MCP server registered in `.vscode/mcp.json` under the name `project-memory`.
You can use these tools directly without running shell commands:

| Tool | What it does |
|------|-------------|
| `search_memory(query, top_k, threshold)` | Semantic search over all documentation |
| `get_memory()` | Read current MEMORY.md (working memory) |
| `update_working_memory(current_task, next_steps, blocked, append_note, clear_completed)` | Update any MEMORY.md section — pass what you want to change, leave the rest empty |
| `add_learning(title, problem, root_cause, solution, key_takeaway)` | Add a lesson to LEARNING.md |
| `add_wiki_entry(heading, content, section)` | Add new entry to WIKI.md (skips if duplicate) |
| `update_wiki_entry(heading, content, section)` | Replace content of an existing WIKI.md entry |
| `expand_wiki_entry(heading, content, section)` | Append content to an existing WIKI.md entry |
| `remove_wiki_entry(heading, section)` | Delete an entire WIKI.md entry block |
| `refresh_index()` | Rebuild Chroma vector index after doc changes |
| `index_status()` | Check vector index health |

## Context Retrieval Rules

1. **MEMORY.md is always loaded** at session start. Read it immediately for current task context.
2. **Do NOT read docs/WIKI.md, docs/LEARNING.md, or docs/features/*.md in full.** Use `search_memory()` instead.
3. **When you need knowledge**, use `search_memory()` (MCP tool) or fall back to:
   ```bash
   python .github/skills/project-memory-vector-db/scripts/retriever.py --query "<your question>" --top-k 5
   ```
   ```bash
   python .github/skills/project-memory-vector-db/scripts/retriever.py --server --query "<your question>" --top-k 5
   ```

   To start the server (keeps model warm, recommended for multiple queries):
   ```bash
   pip install fastapi uvicorn
   python .github/skills/project-memory-vector-db/scripts/retriever-server.py --port 8000
   ```
   Or on Windows: `.\start-server.ps1`

4. After getting search results, read the relevant section using `read_file` with the returned `line_start` and `line_end`.
5. **Read docs/ sections** when: the user asks about architecture/decisions, reports a bug/error, or before making a new design decision.
6. **Update MEMORY.md** as you make progress: mark tasks complete, update blocked items, note pivots.

## Heading Level Standards

Both H2 (`##`) and H3 (`###`) are used as chunk boundaries in the vector index. Use this rule:

### WIKI.md
| Level | When to Use | Example |
|-------|------------|---------|
| **`##`** | A major knowledge domain | `## Architecture Overview`, `## Tech Stack` |
| **`###`** | A sub-topic or decision entry within a `##` section | Under `## Key Decisions`: `### 2026-06-17: Chose PostgreSQL` |

### LEARNING.md
| Level | When to Use | Example |
|-------|------------|---------|
| **`##`** | A new, distinct lesson | `## 2026-06-17: JWT Token Validation Race Condition` |
| **`###`** | An update to an existing lesson | Under existing `##`: `### 2026-06-20 Update: Also affects refresh token` |

### Feature docs (docs/features/*.md)
| Level | When to Use | Example |
|-------|------------|---------|
| **`##`** | A major feature component | `## Payment Flow`, `## Refund Logic` |
| **`###`** | A sub-component or edge case | Under `## Payment Flow`: `### Failed Transaction Recovery` |

## Write Standards

### LEARNING.md — "Check First, Then Write"

When you discover a lesson worth recording:
1. **Search the vector DB** with retriever.py using relevant keywords to check if similar knowledge exists.
2. **Similar section found?**
   - Read the existing section via `read_file`.
   - **Exact same issue?** → Append as `### YYYY-MM-DD Update: [what changed]` under the existing section.
   - **Related but different?** → Create new `## YYYY-MM-DD: Title` at the TOP of the file.
3. **No similar section?** → Create new `## YYYY-MM-DD: Title` at the TOP.
4. Each entry: **Problem / Root Cause / Solution / Key Takeaway**.

### WIKI.md — "Grow Sections, Don't Split Them"
- Fits under existing `##`? Append to end of that section (use `###` for sub-topics).
- No match? New `##` at bottom.
- Key Decisions: new `### YYYY-MM-DD: Title` at top of section.
- Never rewrite/delete without user approval.

### MEMORY.md — "In-Place Update"
- Rewrite `## Current Task` and `## Next Steps` as priorities shift.
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
