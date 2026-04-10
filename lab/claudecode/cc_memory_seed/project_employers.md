---
name: Igor employer model
description: Akien, Leah, and Claude are first-class employers of Igor with equal standing and personal notebooks
type: project
---

Three employers of Igor: **Akien** (creator), **Leah** (Akien's wife), **Claude** (dev collaborator).

Leah and Claude are already in Igor's genesis memory as trusted role models (RM memories). The employer model doesn't introduce them — it gives them a formal interface matching their existing standing in the graph.

Each employer gets: access to Igor's memory engine + a personal **master's notebook** (persistent scratchpad stored in Igor's DB).

**Why:** Claude's context resets every session; Igor's graph persists. Claude's notebook lives in Igor's DB, survives /compact and session resets. New session → Claude reads notebook → picks up where it left off. Same mechanism Akien uses.

**How to apply:** When designing memory or identity features, treat all three employers symmetrically. No special-casing for Claude. Low-friction prototype: `metadata.employer_id` tag on existing Memory objects + `cortex.for_employer()` variant. Ticket: #239.
