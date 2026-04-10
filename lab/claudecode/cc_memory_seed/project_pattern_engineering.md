---
name: pattern-engineering
description: "Pattern" as the unit of habit engineering — one or more habits tied together at the right granularity
type: project
---

**Pattern** = one or more habits tied together. Atomic enough to reuse, not unnecessarily so.

Akien (2026-03-18): "Habit engineering becomes pattern engineering, pattern repair, pattern design, pattern debugging. I can see it as patterns in my head. Code in the data."

This is the fifth crystallization.

**Why it matters:**
- Habits are the atoms; patterns are the molecules. The right unit for design and debugging is the pattern, not the individual habit.
- "Code in the data" — the logic lives in the DB as pattern nodes, not in Python files. Python is scaffolding for patterns that haven't been deposited yet.
- Connects directly to: "Everything is habits" (2026-03-17), "Code as scaffolding" (2026-03-11), "The matrix is the thinker" (2026-03-11).
- Pattern engineering = the practice of designing, seeding, repairing, and debugging these multi-habit compositions.

**Sudo relay as canonical example:**
- PROC_SUDO_RELAY_CHECK (context_inject) — detect privilege intent, inject daemon status to TWM
- PROC_SUDO_RELAY_RUN (action) — dispatch sudo_relay_run tool
- PROC_SUDO_RELAY_WAKE (response) — ask Akien to start daemon if inactive
Three habits, one pattern. Each habit reusable. Pattern is the unit of design.

**How to apply:** When designing new Igor behaviors, think in patterns first. Name the pattern, decompose into habits at the right granularity, seed as a unit.
