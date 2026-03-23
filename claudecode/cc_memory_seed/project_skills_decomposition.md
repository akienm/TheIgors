---
name: Skills decomposition insight
description: Akien's insight about breaking TheIgors workflow into composable Claude Code skills
type: project
---

Workflows like savestate and workstep can be decomposed into multiple smaller skills rather than one monolithic skill. Human-required steps (synthesis, judgment calls) stay as designer skills; mechanical steps become scribe skills with clean handoff via the cc_channel queue.

**Why:** The Igor DB read/write bridge (ops.py: store_decision, store_session_note, queue_task) already exists. Skills can drive those via CC→Igor execute_habit without bash scripts.

**How to apply:** When designing new workflow skills, split at the human/mechanical boundary. Designer skill ends by queuing the scribe task; Scribe skill starts by reading the queue. Log-tracing and DB-query patterns in the `igor` skill are candidates for extraction into focused sub-skills (e.g., `igor-diagnose`, `igor-habit-inspect`).

Akien noted this pattern independently while thinking about exporting TheIgors workflows to other work contexts. He also noted that "skill builder" is an emerging term for this practice — TheIgors was already doing it.
