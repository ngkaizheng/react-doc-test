---
name: project-memory
description: >-
  Manage the project's long-term memory system using MEMORY.md, WIKI.md, LEARNING.md, and AGENTS.md.
  Provides hooks-based context injection at session start and automatic knowledge indexing at session end.
  Run `init.py` to bootstrap the files in a new repo.
  Triggers on: project memory, session context, knowledge management, long-term memory, memory files, wiki, lessons learned, agent rules.
---

# Project Memory Skill

This skill implements a **dynamic context retrieval system** for AI agents working in this repository. It ensures the agent always has relevant context without wasting tokens on unused knowledge.

## File Structure

```
repo-root/
├── project-memory/
│   ├── MEMORY.md        ← Loaded every session (working memory)
│   ├── WIKI.md          ← On-demand (source of truth)
│   ├── LEARNING.md      ← On-demand (lessons learned)
│   └── index.json       ← Auto-generated section index
├── .github/
│   ├── hooks/
│   │   └── memory.json  ← Wires SessionStart + Stop hooks
│   └── skills/
│       └── project-memory/
│           ├── SKILL.md
│           └── scripts/
│               ├── init.py          ← Bootstrap the 4 files
│               ├── session_start.py  ← Reads MEMORY.md → systemMessage
│               ├── indexer.py        ← Parses WIKI + LEARNING → index.json
│               └── templates/
│                   ├── MEMORY.md
│                   ├── WIKI.md
│                   ├── LEARNING.md
│                   └── AGENTS.md
```

## How It Works

### SessionStart Hook
The `session_start.py` script runs automatically at the start of every agent session. It:
1. Reads `project-memory/MEMORY.md`
2. Injects its content as a `systemMessage` so the agent has working context
3. Notifies the agent about the existence of WIKI.md, LEARNING.md, and index.json

### Knowledge Retrieval (On-Demand)
The agent is instructed to:
1. Browse `project-memory/index.json` to discover available knowledge sections
2. Read specific sections using `read_file` with line ranges from the index
3. Only fetch what's relevant — never load WIKI.md or LEARNING.md in full

### Stop Hook
The `indexer.py` script runs automatically at session end. It:
1. Parses WIKI.md and LEARNING.md for H2 (`##`) and H3 (`###`) headings
2. Rebuilds `project-memory/index.json` with section keys, line ranges, and keywords
3. Keeps the index in sync with actual file contents

## Getting Started in a New Repo

```bash
# From the repo root:
python .github/skills/project-memory/scripts/init.py
```

This creates `project-memory/` with starter templates for MEMORY.md, WIKI.md, LEARNING.md, and AGENTS.md.

Then merge or copy the AGENTS.md rules into your root `AGENTS.md` or `.github/copilot-instructions.md`.

## Knowledge Index Format

The indexer generates `project-memory/index.json` with this structure:

```json
{
  "last_updated": "2026-06-17T01:50:00Z",
  "wiki": {
    "architecture-overview": {
      "heading": "Architecture Overview",
      "file": "WIKI.md",
      "line_start": 12,
      "line_end": 45,
      "level": 2,
      "keywords": ["architecture", "overview", "clean"]
    }
  },
  "learning": {
    "jwt-middleware-fix": {
      "heading": "JWT Middleware Fix",
      "file": "LEARNING.md",
      "line_start": 8,
      "line_end": 24,
      "level": 2,
      "keywords": ["jwt", "middleware", "token"]
    }
  }
}
```

## Maintenance

### MEMORY.md
The agent updates this in-place during sessions — rewriting `## Current Task`, checking off items, updating blockers. When all tasks are complete, the agent asks you whether to archive the content to WIKI.md and wipe MEMORY.md for the next feature cycle.

### WIKI.md — "Grow Sections, Don't Split Them"
Append-and-grow only. New information is added to existing `##` topic sections (with `###` sub-headings for distinct sub-topics). If no existing section fits, a new `## Section` is added at the bottom. `## Key Decisions` entries (formatted as `### YYYY-MM-DD: Title`) always go at the top of that section. Never rewrite or delete content without user approval.

### LEARNING.md — "Check First, Then Write"
Reverse-chronological entries at the top. Before writing, the agent checks `index.json` for matching keywords:
- **Exact same issue?** → No new `##` entry. Appends as `### YYYY-MM-DD Update:` under the existing section.
- **New issue?** → New `## YYYY-MM-DD: Title` at the top.

All entries use the format: **Problem / Root Cause / Solution / Key Takeaway**.

### Heading Levels (Both Files)
| Level | Purpose |
|-------|---------|
| `##` | Major topic (WIKI) or distinct lesson (LEARNING) |
| `###` | Sub-topic or update entry within a `##` section |

Both levels are indexed in `index.json` for discoverability.

### index.json
Auto-regenerated at every session end by the `Stop` hook. No manual editing needed.

## Scripts Reference

| Script | When to Run | What It Does |
|--------|-------------|-------------|
| `init.py` | New repo setup | Creates the 4 template files in `project-memory/` |
| `session_start.py` | Automatically (SessionStart hook) | Reads MEMORY.md → outputs systemMessage |
| `indexer.py` | Automatically (Stop hook) | Parses WIKI.md + LEARNING.md → rebuilds index.json |
