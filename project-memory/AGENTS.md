# Agent Rules — Project Memory

<!--
This file defines how the agent should interact with the project memory system.
Merge these rules into your root AGENTS.md or .github/copilot-instructions.md.
-->

## Context Retrieval Rules

1. **MEMORY.md is always loaded** at session start. Read it immediately for current task context.
2. **WIKI.md and LEARNING.md are loaded on-demand only.** Do not read them in full at start.
3. **Always check `project-memory/index.json` first** when you need architectural context or troubleshooting knowledge. Browse the index to find relevant sections, then use `read_file` with the specified line ranges.
4. **Read WIKI.md sections** when: the user asks about architecture/decisions, or before making a new design decision.
5. **Read LEARNING.md sections** when: the user reports an error or unexpected behavior, or when debugging a known issue.
6. **Update MEMORY.md** as you make progress: mark tasks complete, update blocked items, note pivots.

## Heading Level Standards

Both H2 (`##`) and H3 (`###`) are indexed in `index.json`, so the agent can discover and retrieve them. Use this rule to decide which level:

### WIKI.md
| Level | When to Use | Example |
|-------|------------|---------|
| **`##`** | A major knowledge domain or broad topic area | `## Architecture Overview`, `## Tech Stack`, `## Coding Standards` |
| **`###`** | A specific sub-topic, decision entry, or detail within a `##` section | Under `## Key Decisions`: `### 2026-06-17: Chose PostgreSQL over MySQL` |

### LEARNING.md
| Level | When to Use | Example |
|-------|------------|---------|
| **`##`** | A new, distinct lesson that doesn't overlap with existing entries | `## 2026-06-17: JWT Token Validation Race Condition` |
| **`###`** | An update to an existing lesson (same root cause, new detail) | Under an existing `##` entry: `### 2026-06-20 Update: Also affects refresh token flow` |

## Write Standards

### LEARNING.md — "Check First, Then Write"

When you discover a lesson worth recording:
1. **Check `index.json`** for existing sections with matching keywords.
2. **Similar section exists?**
   - Read the existing section.
   - **Exact same issue?** → Do NOT create a new `##` entry. Append as `### YYYY-MM-DD Update: [what changed]` under the existing section.
   - **Related but different?** → Create a new `## YYYY-MM-DD: Title` at the TOP of the file.
3. **No similar section?** → Create a new `## YYYY-MM-DD: Title` at the TOP of the file (reverse chronological).
4. Each entry must follow this format:

   ```markdown
   ## 2026-06-17: Descriptive Title

   **Problem:** What went wrong.

   **Root Cause:** Why it happened.

   **Solution:** How it was fixed.

   **Key Takeaway:** What to remember for next time.
   ```

### WIKI.md — "Grow Sections, Don't Split Them"

When you have permanent knowledge to record (with user confirmation):
1. **Does it fit under an existing `##` topic section?**
   - **Yes** → Append the new information at the END of that existing section. If it's a distinct sub-topic within the section, wrap it as a `###` sub-heading.
   - **No** → Create a new `## Section Name` at the BOTTOM of the file.
2. **Key Decisions** are special: always add a new `### YYYY-MM-DD: Decision Title` entry at the TOP of the `## Key Decisions` section.
3. **Never rewrite or delete** existing content without asking the user first. The wiki is append-and-grow only unless the user explicitly says something is outdated.

### MEMORY.md — "In-Place Update"
- Rewrite `## Current Task` and `## Next Steps` as priorities shift.
- Mark `[ ]` as `[x]` when items are done.
- Never delete completed items until the user agrees to wipe the file for a new feature cycle.

## Subagent Protocol

When spawning any subagent:
1. Include the relevant sections from MEMORY.md and any applicable WIKI/LEARNING context in your prompt.
2. Demand structured output: "Return your findings with: [completed], [discoveries], [blockers], [output]."
3. After the subagent returns, capture any learnings into LEARNING.md and update MEMORY.md progress.

## Session End

When the session is ending:
- If all tasks in MEMORY.md are completed, ask: "All tasks in MEMORY.md are complete. Should I archive this content to WIKI.md and clear MEMORY.md for the next feature?"
- Otherwise, ensure MEMORY.md accurately reflects current state for the next session.
