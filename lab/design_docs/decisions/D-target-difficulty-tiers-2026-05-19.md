# D-target-difficulty-tiers-2026-05-19
**title:** Ticket difficulty tiers — Apprentice/Sustainer/Creator/Master/Teacher capability routing
**date:** 2026-05-19
**status:** open
**spawned_tickets:** T-ticket-difficulty-schema, T-queue-next-difficulty, T-igor-difficulty-cap

## Decision narrative
Add `target_difficulty: int` (1-5) to the ticket schema so consumers self-select tickets at or below their capability level. Tier scale: Apprentice(1/Igor), Sustainer(2/Librarian), Creator(3/Haiku), Master(4/Sonnet), Teacher(5/Opus). Igor's daemon passes `--max-difficulty=1` to `cc_queue.py next` so he only claims Apprentice-tier tickets; harder work sits pending until a capable consumer picks it up.

Alternative considered: using the existing `worker=` field (doesn't generalize to capability routing, hardcodes destination) or ticket tags (unreliable, not machine-filterable). Chose difficulty field because it's explicit, range-validated, and generalizes across all consumers without per-consumer tag logic.

## Hypothesis
Igor never claims tickets with target_difficulty > 1 after the feature ships; high-difficulty tickets sit pending until a higher-tier consumer claims them.

## Measurement Signal
2-hour spot-check (approx 21:30 UTC 2026-05-19): workspace not crudded up = shipped and working. `cc_queue.py list --worker=igor` shows no difficulty>1 tickets in Igor's sprint history.

## Goal Link
none: direct system self-regulation — reduces cleanup cycles from over-claimed tickets, not tied to a named G-xxx goal yet.
