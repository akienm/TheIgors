# D-worker-mode-routing-2026-04-21 — Route worker dispatch by ticket metadata

**Date:** 2026-04-21
**Status:** open
**Decision type:** architecture / orchestration

## Summary

Route worker dispatch by ticket `worker` field (values: `claude` | `igor`), not unconditional retirement of `worker_foreman`. Default `worker=igor` (in-process via engram chain, cheap, Qwen-routable); opt-in `worker=claude` (konsole-spawned CC session) for HIGH-inertia, parallel, Claude-required, or safety-isolated work.

The 2026-04 retirement in `WorkingWithClaude.md` rested on `ENGRAM_CODE_*` being functional — audit area_2 (Pass 2, 2026-04-20) confirmed it's structurally dead (trigger/cell name mismatch, unregistered MCPCALL targets, two habits reference nonexistent `run_engram_cursor`). That changes the cost/benefit: the retirement path has been aspirational, not operational.

## Rationale

Akien 2026-04-21: "maybe it wasn't valid for all cases?" The retirement was overgeneralized. Cases where konsole-spawn still earns its keep:
1. HIGH-inertia tickets — a reviewable CC session, not silent in-process work on `models.py`
2. Long work exceeding TWM capacity — pe_chain is token-limited
3. Parallel work — konsole fans out; in-process is serial
4. Mixed-model routing — spawn Claude for hard tickets, run Qwen-via-pe_chain for cheap ones
5. Safety isolation — a mistake in a separate CC session doesn't corrupt Igor's TWM/session state

So both paths stay; `worker` field picks.

## Biomimicry

Default-to-igor is the honest biomimetic position: a cognitive agent does its own work through its own reasoning loop, not by spawning a separate agent. Default-to-claude for HIGH-inertia is a pragmatic concession to reviewability, not a biological claim.

## Spawned tickets

- `T-worker-dispatch-routing` (M) — schema defaults + PROC_WORKER_FOREMAN routing logic; gated on `T-engram-trigger-cell-name-mismatch`
- `T-engram-trigger-cell-name-mismatch` (S, **critical**) — fix trigger/cell name mismatch + add `run_engram_cursor` wrapper
- `T-engram-mcpcall-register-pe-steps` (S) — register the 12 per-step pe_* functions as MCPCALL tools
- `T-verify-pe-chain-qwen-tier` (S) — verify pe_chain routes to cheap background tier (Qwen), not interactive (Claude)
- `T-worker-dispatch-validation` (M) — end-to-end validation on a seeded test ticket; gated on all four above

Decision closes automatically when all five land.

## Follow-ups (not tickets yet)

- Flipping the default `worker` field to `igor` after validation succeeds — separate decision, not this one
- Retiring `worker_daemon.sh` after validation proves the igor path stable across N tickets — separate decision
- Updating `WorkingWithClaude.md` to reflect "route by metadata" instead of "retired 2026-04" — part of `T-worker-dispatch-routing`

## Pointers

- Pass 2 area_2 report: `lab/design_docs/audit_2026/pass2_output/area_2_engrams_habits_pe.md` (Gap 1)
- Pass 2 aggregate: `lab/design_docs/audit_2026/pass2_output/AGGREGATE.md`
- Prior "retirement" narrative: `lab/design_docs/WorkingWithClaude.md`
- Foreman tool: `wild_igor/igor/tools/worker_foreman.py`
- Foreman habits: `seed_worker_foreman.py`, `seed_foreman_habit.py`
