# Lessons Learned

## 2026-06-17: get_or_create_collection() Bug — Duplicate Function & Unconditional Delete

**Problem:** The `get_or_create_collection()` function in `indexer.py` unconditionally deleted the existing Chroma collection on every call, destroying the vector index. Also, the function was duplicated — two identical copies existed in the same file.

**Root Cause:** A past edit likely created a duplicate during refactoring. The dimension-mismatch check was intended but never implemented — the `if col.name == "project-memory"` block always hit the `delete_collection()` call and the `break` prevented any other collections from being checked.

**Solution:** 1. Removed the duplicate function (lines 256-315). 2. Added a proper dimension check: only delete if `col.metadata["embedding_dimensions"]` differs from the current model's dimensions. 3. Added a fallback in `mcp-server.py`'s `refresh_index()` that re-calls `init_model()` if `collection` is None, preventing empty-collection creation from the inspector tool.

**Key Takeaway:** The MCP Inspector spawns a fresh process — `init_model()` may not complete before the first tool call. Always ensure `refresh_index()` defends against `collection is None`. And never unconditionally delete Chroma collections; always check dimension compatibility first.


## 2026-06-17: MCP Server Requires Restart After Code Changes

**Problem:** Fixed the `add_wiki_entry` formatting bug in `memory.py`, but the fix didn't take effect. The MCP tool was still producing broken markdown with concatenated entries.

**Root Cause:** The MCP server is a long-running Python process managed by VS Code. It imports all modules at startup and caches the bytecode in memory. Editing the source `.py` files does NOT hot-reload the server.

**Solution:** Restart VS Code (Reload Window) or restart the Extension Host. After restart, the MCP server re-imports all modules and picks up code changes. Always run `refresh_index()` after restart to verify the server is responding.

**Key Takeaway:** Any edit to `memory.py`, `mcp-server.py`, or other Python scripts requires an MCP server restart (Reload Window or Restart Extension Host). Edits to markdown docs (WIKI.md, LEARNING.md) don't — just run `refresh_index()`.


## 2026-06-17: append_wiki_entry MCP Tool Lacked Proper Newline Spacing

**Problem:** Using add_wiki_entry MCP tool to append entries under a ## section resulted in entries getting concatenated without blank line separators, and content bleeding into the next section heading (e.g., `...property.## Coding Standards`).

**Root Cause:** In memory.py's append_wiki_entry(), the entry template was `f"\n### {heading}\n{content}"` — only a single \n before the heading (needs \n\n for a blank line), and no trailing \n after content (so the content bleeds into the next ## section since m.group(0).rstrip() removes the trailing whitespace that separated sections).

**Solution:** Changed the entry template to `f"\n\n### {heading}\n{content}\n\n"`: \n\n before ### ensures a blank line separator from previous content, and \n\n after content ensures a blank line before any following ## section heading.

**Key Takeaway:** When using regex to find/replace section content in markdown, always ensure entry templates have \n\n (blank line) both before AND after the entry content. The m.group(0).rstrip() strips all trailing whitespace, so all required newlines must be in the replacement string.


<!--
Record tricky bugs, non-obvious solutions, and edge cases discovered during development.
Each ## section becomes an entry in index.json, discoverable by the agent.

When you encounter a new lesson, add it at the TOP of this file for recency.
-->

## YYYY-MM-DD: Title of the Lesson

**Problem:** What went wrong or what needed solving.

**Root Cause:** Why it happened.

**Solution:** How it was fixed.

**Key Takeaway:** What to remember for next time.
