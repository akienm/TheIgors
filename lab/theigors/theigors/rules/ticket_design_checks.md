# Ticket design checks — filing-time positive checks for /review Mode A

**Path:** `theigors/rules/ticket_design_checks`
**Updated:** 2026-04-21T19:42:54.171707+00:00 by T-palace-ticket-design-rules

Check-shaped entries that /review Mode A loads at ticket filing time
to verify each draft positively against Akien's design rules. The
shape is a scaffold, not a correction: the check is present when the
drafter needs it.

Content shape (each child):

    applies_when: |
      <natural-language predicate — when does this check fire?>
    check_body: |
      <what the ticket draft must contain>
    failure_message: |
      <AMEND guidance if check fails — goes into /review output>

Narrative source lives at theigors/rules/<name> (human-reading).
Check shape lives here (machine-consumable by /review).

Entry index:
  - no-sqlite                 (narrative: theigors/rules/database)
  - oop-first                 (narrative: theigors/rules/coding)
  - docs-in-code              (narrative: theigors/rules/docs-live-in-code)
  - no-new-memory-schemas     (narrative: theigors/rules/memory)
  - test-plan-or-why-not      (narrative: theigors/rules/coding)

Decision: D-scaffold-not-correct-2026-04-21.


## Pointers

- **child:** `theigors/rules/ticket_design_checks/no-sqlite`
- **child:** `theigors/rules/ticket_design_checks/oop-first`
- **child:** `theigors/rules/ticket_design_checks/docs-in-code`
- **child:** `theigors/rules/ticket_design_checks/no-new-memory-schemas`
- **child:** `theigors/rules/ticket_design_checks/test-plan-or-why-not`
- **decision:** `D-scaffold-not-correct-2026-04-21`
