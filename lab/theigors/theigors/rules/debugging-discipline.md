# Debugging discipline — log line and regression test ship with the fix

**Path:** `theigors/rules/debugging-discipline`
**Updated:** 2026-05-01 by claude-haiku-4.5

Always add both the log line that would have pointed at the bug AND the regression test that captures the failure mode — alongside the fix, in the same commit. The discipline pays for itself: never dig deeply for the same thing more than once.

The shape of a debug commit:
1. Find the bug.
2. Before fixing — note what log line would have surfaced this immediately. Add it (WARNING when silent-return-False / fanout=0 / unexpected-empty paths). Surrounding state goes in the log message; future occurrences are visible at a glance.
3. Write the regression test that captures the failure mode. The test fails on the unfixed code (verify), passes after the fix.
4. Apply the fix.
5. Commit all three together.

Why both, not one:
- A log line alone catches recurrence but doesn't prevent it.
- A test alone prevents recurrence but doesn't help when the test misses the next variant.
- Together: visible in production AND gated against in CI.

Applies to: every editor — CC, Igor, future agents. Holds across HIGH/MED/LOW inertia tiers.

Pairs with `theigors/rules/coding` (inertia gates the edit shape) and the audit step that registers persistent forever-checks via `audit_add.py` (when a class of bug deserves systemic guardrails, register the check).

revision: 2026-05-01 — Akien framing during /fixit pre-sprint-filter sweep
