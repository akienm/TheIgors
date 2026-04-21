---
id: D-scaffold-not-correct-2026-04-21
date: 2026-04-21
status: open
spawned_tickets:
  - T-palace-ticket-design-rules
  - T-ticket-template-structured
  - T-review-loads-palace-rules
  - T-review-build-tightness-grade
---

# D-scaffold-not-correct-2026-04-21 — Shift design rules from implicit to explicit-at-filing-time

## Summary

Make Akien's implicit design rules (no-sqlite, OOP-first, docs-in-code, no-new-memory-schemas, test-plan-or-why-not) explicit at the moment a ticket is drafted. Palace holds the rules in check-shape; `/ticket` prompts for the fields each rule needs; `/review` verifies tickets positively against the rules at filing time; a build-tightness grade tells us whether a ticket is tight enough for a cheaper builder.

## Narrative

Tonight's conversation — carried over from the post-compact topic break. Akien's frame: best-practices structures in Igor are his doing, not Claude's; more design-in-ticket produces better code; the lever isn't a more expensive model so much as making the rules visible at the point-of-use. The sqlite banner worked for that reason, not because Claude's defaults changed.

Key reframe: "drift" is the wrong word for Claude's defaults meeting unspecified terrain. Scaffold beats correction. Making rules present at filing time lets Claude's want-to-be-thorough and want-to-satisfy lean against each other productively inside a tight scope — the same mechanism Akien uses on himself (two negatives leaned to make a positive).

Concrete chain:

1. Palace rules must be check-shaped (applies_when, check_body, failure_message) — not just narrative — before any reader can consume them as checks.
2. `/ticket` must ask for the structured fields those checks need (test plan, affected files, design rules, scope boundary), because free-form description lets drafters skip the check.
3. `/review` filing-time must load the palace checks and verify tickets positively, not just run its current generic negatives.
4. A build-tightness grade makes the "could a cheaper builder ship this?" bar explicit, so loose tickets bounce back to design rather than shipping.

## Scope boundary

- No DB schema changes in cc_queue — structure lives in description (or a parallel payload within it).
- Does not touch `/review`'s standalone plan/code/PR modes (Mode B).
- Dispatch-category rules and observe-ticket rules are a separate track (already captured in `feedback_no_immobile_observe_tickets.md`); this decision is specifically about design-rule scaffolding at filing.

## Related memories

- `feedback_scaffold_not_correct.md` — the reframe that drove this decision
- `feedback_no_immobile_observe_tickets.md` — adjacent rule, same shape (make the constraint visible)
- `project_three_pass_audit_shape.md` — this work is pre-Pass-3 cleanup, sharpens the review bar for the remaining 149
