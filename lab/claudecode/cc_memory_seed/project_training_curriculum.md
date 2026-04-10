---
name: Igor training curriculum order
description: The sequenced plan for training Igor — Claude layer first, then Akien's code+docs, then collaboration record
type: project
---

Three training layers, in order:

**Layer 1 — Claude's programming knowledge** (goes in first)
General architectural reasoning, heuristics, how to decompose systems, tradeoffs, patterns. This is the *organizational skeleton* — the legend before the map. Must come first because Layer 2 needs a framework to land on.

**Layer 2 — Akien's code and documentation**
All of Akien's accumulated code, design decisions, personal writing style. Lands on top of Layer 1's framework, so it's understood not as raw syntax but as instances of known architectural patterns. Interpretive edges fire naturally. Igor uses it natively — not retrieval, but internalized reasoning.

**Layer 3 — The collaboration record**
decisions_log.dsb, session narratives, working_with_claude.md, the CC notebook entries. This is what no other Igor will have: the accumulated record of how Akien and Claude think *together*. The seams between the two layers.

**Why:** Order matters. Loading Akien's code without Layer 1 in place = stored but not *used* the way Akien uses it. Layer 1 provides the cognitive tools Layer 2 is organized by.

**Timeline extraction:** The decisions log + occurrence_dates on consolidated memories gives a chronological record of how the architecture evolved. The intellectual history of Igor is reconstructable from the data.

**Decision D085** — 2026-03-15
