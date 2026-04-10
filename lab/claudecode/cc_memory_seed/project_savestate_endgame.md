---
name: Savestate endgame — dissolves into continuous pipeline
description: The mature state where savestate ritual is replaced by per-action DB saves and Igor-driven context injection
type: project
---

Savestate exists only because nothing saves automatically. The end state: every action that matters trips a tiny DB write in real-time. By session end there's nothing to flush — it's already in Igor's DB.

**How it lands:**
- Decision made → `store_decision` fires at that moment (skill step, not end-of-session)
- Gap closed → DB entry updated by the step that closes it
- Ticket changed → Igor habit logs it during the work, not after
- Session context → Igor's ring memory + episodic nodes, not sessions.md
- Context reload → Igor traverses project subgraph (D110), hands Claude the relevant narrative path via context_inject habit

**Sessions.md, gap_analysis.md, decisions_log.dsb** become read-only audit artifacts or human-readable exports Igor generates on request. The DB is the truth.

**The skill pipeline accelerates this:** each skill step calls the right Igor habit to save state for that step. Savestate skill becomes "are there any unsaved bits?" — usually no.

**D110 (project self-model + log-to-DB)** is the key enabler — once Igor has a traversable project graph, context injection replaces file reads at session start.

**Why:** Savestate is a workaround for a stateless workflow. The skills pipeline + Igor DB integration closes the gap step by step until the ritual has nothing left to do.
