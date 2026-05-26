# D-worker-daemon-retired-2026-05-25
**title:** Retire worker_daemon.sh — /query-ticket is the canonical path, no autonomous sprinting
**date:** 2026-05-25
**status:** open
**spawned_tickets:** T-retire-worker-daemon-sh, T-consequence-worker-daemon-retired

## Decision narrative
worker_daemon.sh was auto-sprinting migration tickets in parallel with CC, violating the principle that no autonomous code work should proceed until Igor's reasoning is stabilized. The daemon is suspended as of 2026-05-25. Formally retire it by adding a disabled sentinel and removing the `claim` command from cc_queue.py entirely (LegacyDirectClaimError). /query-ticket is the single canonical read-only path for "what's next?" and will transparently switch to the ADC queue device MCP interface when that ships.

## Hypothesis
No autonomous ticket consumption is possible via worker_daemon.sh or cc_queue.py claim; /query-ticket is the documented single path.

## Measurement Signal
`cc_queue.py claim T-test` prints LegacyDirectClaimError; worker_daemon.sh loop is commented out; /query-ticket referenced in SPRINT.md, CONTEXT-LOAD.md, CLAUDE.md.

## Goal Link
none: prerequisite safety gate before ADC queue device work proceeds; not tied to a growth goal but to a stability constraint.
