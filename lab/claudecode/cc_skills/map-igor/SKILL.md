---
name: map-igor
description: On-demand inspection snapshot of Igor's full state. Produces ~/.TheIgors/maps/igor-map-<YYYY-MM-DD-HHMMSS>.json plus a one-screen stdout summary. Sections cover palace tree, rules, subsystem index, tickets, slates, decisions, gates, MCP, IMAP, channels, inbox, logs, startup reads, DB schema, runtime, code map, and processes. Diff mode with --since=yesterday. Model: Haiku (I/O-bound, no reasoning load).
model: haiku
---

# /map-igor — Full Igor state snapshot

One command, one file, one screen. When you need to understand what's
running, what's broken, or how today's state differs from yesterday's.

## Usage

```bash
python3 ${CC_WORKFLOW_TOOLS}/map_igor.py
python3 ${CC_WORKFLOW_TOOLS}/map_igor.py --since=yesterday
python3 ${CC_WORKFLOW_TOOLS}/map_igor.py --section=tickets
```

Output file: `~/.TheIgors/maps/igor-map-<YYYY-MM-DD-HHMMSS>.json`
Stdout: one-screen summary (the file has the detail).

## Sections

| Section | Source |
|---------|--------|
| palace_tree | memory_palace table — paths, titles, types, child counts |
| rules | theigors/rules/* nodes full content |
| subsystem_index | theigors/subsystem_index node |
| tickets | queue.json — open by status, with size + inertia tags |
| slates | today's + last 3 days slate files |
| decisions | last 30 lines of decisions_log.dsb |
| gates | igor.switches.cfg — all IGOR_* flags + state |
| mcp_servers | ~/.claude/settings.json MCP section |
| imap_buses | ~/.TheIgors/Igor-wild-0001/ IMAP config |
| channels | cc_channel config + last 24h message count |
| inbox | cc_inbox.jsonl — unread by kind/urgency |
| logs | ~/.TheIgors/*/logs/*.log — paths, sizes, last-modified |
| startup_reads | files Igor reads at boot (.env, cfg, switches) |
| db_schema | memory_palace + memories + twm_observations table stats |
| runtime | ~/.TheIgors/ tree sizes + process list |
| code_map | wild_igor/ top-level dirs + primary file per area |
| processes | Igor tmux sessions, Ollama instances, MCP server PID |

## Diff mode

```bash
python3 ${CC_WORKFLOW_TOOLS}/map_igor.py --since=yesterday
```

Compares current snapshot against the most recent prior map in
`~/.TheIgors/maps/`. Outputs only sections where something changed.
Useful at day-close to see what actually moved.

## Single-section mode

```bash
python3 ${CC_WORKFLOW_TOOLS}/map_igor.py --section=tickets
```

Runs only one section. Faster, less noise.

## Hard rules

- Output file is always written; stdout is always the one-screen summary.
- Snapshot files are kept for 14 days, then auto-expired.
- Never writes to DB, palace, or queue — read-only snapshot tool.
- Snapshot size < 1MB typical. Files > 10MB indicate a data-collection bug.
