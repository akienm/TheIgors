---
name: mac_epic
description: D109 — Multi-attention-center reading: memory delegation + ebook_reader → internal habits
type: project
---

D109 — Multi-attention-center reading epic. Epic (large, probably multiple tickets).

**Goal**: Main Igor attention center can surface a memory (even a new one) in a remote attention center, which picks it up as a task and executes it. Primary use case: reading delegation.

**Akien's framing**:
- "The design calls for an attention center to be able to surface a memory, even a new one, in other attention centers."
- "This is to allow the main igor to have another attention center do a task. And the tasks I have in mind are reading."
- "What in our external reader file will all have to move to internal habits." — large, epic scope.
- Target: "by the end of tomorrow, I'd like to have that working" — refers to basic delegation working, not full migration.

**Architecture (extends D093)**:
- D093 already designed NetworkDatabaseProxy (POST /api/db on main port 8080)
- New: main instance writes a TASK memory with target_instance; remote instance polls for its tasks; picks up, executes, writes memories back
- Reading tasks: main Igor creates PROC memory "read this URL" → remote instance's habit fires → start_foreground_reading() on remote → memories write back through NetworkDatabaseProxy

**ebook_reader → internal habits migration**:
- Currently ebook_reader.py is ~1500 lines of direct tool logic
- Long-term: all reading behaviors driven by PROCEDURAL habits, not direct Python dispatch
- D107 started this (PROC_READ_NOW → start_foreground_reading)
- Full migration: large epic, multi-session

**Tickets to create**:
- S: Memory delegation mechanism (main writes task memory with target_instance; remote polls)
- M: Remote instance boot configuration (connects to main DB via NetworkDatabaseProxy)
- L: ebook_reader.py → internal habits migration (full epic)

**How to apply:** When starting this epic, scope "by end of tomorrow" as: basic delegation working (main writes task, remote executes). Full ebook_reader migration is separate epic child.
