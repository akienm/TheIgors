---
name: Multi-session CC architecture + context-load skill
description: Shared channel as coordination substrate, blob-as-trail for startup context, sprint skill design, exportable to non-Igor projects
type: project
---

## Architecture (2026-03-19)

**The sweet spot:** shared infrastructure + ephemeral workers

- **Postgres** — external, always running, all processes share it
- **Web channel** — extract from igor.main, becomes permanent shared channel
- **Igor** — optional matrix substrate, can restart without killing the channel
- **CC sessions** — ephemeral workers, visible terminals, coordinate via channel

**Channel extraction (T-channel-extract):**
Today: CC → POST /api/cc_send → Igor must be running
After: CC → POST /channel → Postgres → Igor optional
All participants (Igor, Claude Code sessions, Akien) in same room regardless of what's up.

**Sprint skill flow:**
Session starts → announces to channel → reads ticket from queue → does work →
posts progress to channel (visible to all) → writes result → exits

## Context-load skill (T-context-load-skill)

**The blob-as-trail insight:**
A prepend-only log IS a trail. Newest at top = recency bias built in.
Read from top until you have enough context, stop. You never need the cold bottom.

**Startup ritual becomes:**
1. Read slate (5 lines — what's active)
2. Slate points to relevant blobs
3. Read top N lines of each blob
4. Done. ~60 lines total. Laser focused.

**Replaces:** reading CLAUDE.md + MEMORY.md + sessions.md + gap_analysis + decisions_log at session start.

**Exportable:** no Igor, no Postgres required. Works on files. Any project that prepends to logs gets this for free.

**Blob naming convention:** TBD in T-context-load-skill design — needs: where's the slate, what's the blob naming convention, how does a session find relevant blobs without prior knowledge.

## Connection to Trails primitive
The blob IS a trail through time. Same primitive as node activation trails, different substrate.
Ring memory, decisions log, session notes, channel messages — all trails, all prepend-newest-first,
all readable top-down until context is sufficient.
