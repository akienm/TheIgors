# D-adc-db-review-tools-2026-05-08
**title:** Database review/browse/edit tools for palace trees and shared tables
**date:** 2026-05-08
**status:** open
**spawned_tickets:** T-librarian-palace-mcp-tools, T-palace-cli

## Decision narrative

Akien needs the same review/browse/edit capability for palace trees that Igor
has for his memories. Two surfaces solve this cleanly:

1. **In-session (MCP tools)**: Add 4 Librarian MCP tools — `palace_ls`,
   `palace_read`, `palace_write`, `palace_delete` — usable directly inside CC
   without leaving the session. Covers the palace tree specifically.

2. **Out-of-session (CLI)**: A `palace_cli.py` script with tree-view, search,
   read, and edit subcommands. Human-friendly terminal output (indented tree,
   truncated content preview). Covers bulk review and offline edits.

Off-the-shelf tools (pgAdmin, TablePlus, psql) already serve flat tables well;
they don't need custom tooling.

---

## Problem statement

The palace stores hierarchical nodes at paths like:
```
palace.decisions.D-foo-2026-05-08
palace.shared.akien.goals
palace.projects.unseen_university.summary
palace.days.20260508
```

Existing tools (`db_query`, `db_dispatch`) allow raw SQL but require knowing
the schema. What's missing:

- **Tree traversal**: "show me everything under palace.projects.*"
- **Path-aware read**: "read palace.shared.akien.goals in full"
- **Inline edit**: "update the content of palace.projects.unseen_university.summary"
- **Tag-based search**: "find all nodes tagged ['decision', 'adc']"

---

## Proposed solution

### Surface 1 — Librarian MCP tools (in-session)

Four new tools in `UnseenUniversity/devices/librarian/tools/palace_tools.py`:

**`palace_ls(prefix="", limit=50)`**
List all nodes under a path prefix, indented tree view:
```
palace.projects
  palace.projects.unseen_university
    palace.projects.unseen_university.map          [doc]    2026-05-08
    palace.projects.unseen_university.summary      [doc]    2026-05-08
    palace.projects.unseen_university.standards    [doc]    2026-05-08
  palace.projects.theigors                        [pointer] 2026-05-08
```

**`palace_read(path)`**
Return full node content for a given path:
```
path:      palace.shared.akien.goals
title:     Akien's Goals Tree
node_type: doc
updated:   2026-05-08T14:16Z
tags:      [shared, akien]
---
ROOT: 'Akien makes the world suck less' ...
```

**`palace_write(path, title, content, node_type="doc", tags=[])`**
Upsert a node. Returns the written path + updated_at.
Requires explicit node_type to prevent accidental type changes.

**`palace_search(query, tags=[], limit=10)`**
Full-text + tag filter search. Uses existing GIN indexes.
Returns list of {path, title, snippet}.

These 4 tools live alongside the existing Librarian tools and are exposed
via the `igor` MCP server (same entry point).

### Surface 2 — CLI script (out-of-session)

`scripts/palace_cli.py` with subcommands:

```bash
# Tree view
python3 scripts/palace_cli.py ls palace.projects
python3 scripts/palace_cli.py ls                     # full tree

# Read a node
python3 scripts/palace_cli.py read palace.shared.akien.goals

# Search
python3 scripts/palace_cli.py search "capability extraction"
python3 scripts/palace_cli.py search --tag decision --limit 20

# Edit (opens $EDITOR or takes --content inline)
python3 scripts/palace_cli.py edit palace.projects.unseen_university.summary
python3 scripts/palace_cli.py edit palace.foo --content "new content" --title "New Title"

# Delete (with confirmation prompt)
python3 scripts/palace_cli.py delete palace.foo.bar
```

Output is human-readable by default; `--json` flag for scripting.

### What off-the-shelf covers

- **psql / pgAdmin / DBeaver**: flat tables (clan.memories, instance.ring_memory,
  clan.traces, etc.). No custom tooling needed — `db_query` + `db_dispatch` MCP
  tools already cover these from inside CC sessions.

---

## Design rules applied

- Palace DB always (adc.palace); no SQLite.
- palace_write uses `ON CONFLICT (path) DO UPDATE` — always upsert, never bare INSERT.
- palace_delete is soft-confirmed (requires explicit `--yes` flag or y/n prompt).
- MCP tools stay in Librarian device boundary; no TheIgors imports.

---

## Spawned tickets

- **T-librarian-palace-mcp-tools** (S): Add palace_ls, palace_read, palace_write,
  palace_search to Librarian tools. Wire into MCP tool list.
- **T-palace-cli** (M): Build `scripts/palace_cli.py` with ls/read/search/edit/delete
  subcommands.
