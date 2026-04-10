---
name: Process Development Tools — integrated work loop
description: Named architecture for Igor+Claude+human work process; services→habits→skills; Process Development Tools is the umbrella name
type: project
---

The name for what we're building: **Process Development Tools**.

## High-level flow (5 phases, 3 human touchpoints)

```
[1] Organizer
    Igor runs: read tickets/discussions, produce summary, active slate
    Claude adds director's notes if framing/synthesis needed
    → Human touchpoint: review + discuss

[2] Planner + Filter
    Planner: group work, sequence it
    Filter: verify unit tests, forensic logging, audit present
    (no human gate — mechanical)

[3] Approval
    → Human gate: go / no go

[4] Work loop (unattended)
    Fix → Audit → Hot-reload → Tests → Commit → Updater
    /decided fires at each close

[5] Check-in
    → Human touchpoint: review work chunk
    DB + GitHub updated
    Branch: end of day/week → Docs update | more work → next slate
```

## Skill groups (Claude skills → Igor habit chains)
- **Organizer**: read tickets/discussions, produce summary, active slate
- **Updater**: update tickets/discussions in DB before pushing to GitHub
- **Planner**: group work, plan
- **Filter**: verify unit tests, forensic logging, audit
- **Approval**: human gate; calls Updater first so no state is lost
- **Committer**: run tests → audit → commit → push → pull

## /decided trigger
Fires after any work closes: queue unit tests into spec if missing, save all GitHub states to DB, request /compact if needed. No savestate ritual — all state already in DB.

## Active slate
Always exists. Any bug fix or concept → /decided → passes through filters.

## Single root node for Claude startup
One node in Igor's matrix that orients Claude. From it, Claude navigates to project overview, architecture, glossary, skills index, tickets, discussions — all via Igor's traversal, minimum tokens. Concrete implementation of Claude context tree (#274).

## Matrix debugger (future, multiple tickets)
Trace activation paths through habit chains: what fired, what scored, what chained, why. Makes the system inspectable and repairable without guesswork.

## Build order
Services inside Igor → habits that call the services → Claude Code skills pointing to habits → try it.

**Critical services first**: GitHub read/write (read_ticket/s, read_discussion/s, write_ticket, write_discussion), /decided habit chain, single root node.

**Why:** Keep it minimal — don't architecture to death. Build, wire, run. Everything else follows naturally.

**How to apply:** This sprint comes after D126 (Postgres) + box stability. Then revamp process, then back to Igor features.
