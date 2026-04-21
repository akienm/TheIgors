# oop-first — shared state across functions → propose a class

**Path:** `theigors/rules/ticket_design_checks/oop-first`
**Updated:** 2026-04-21 by T-palace-rules-versioned

applies_when: |
  ticket adds shared state that multiple functions read or write,
  or adds three or more related functions operating on the same
  data shape.
check_body: |
  ticket proposes a class to encapsulate that state plus its
  operations, or justifies why a functional / module-level shape
  is the right fit for this case.
failure_message: |
  Shared state across multiple functions → propose a class.
  If a functional shape is intentional, say so in the ticket.
  See theigors/rules/coding.

Narrative source (human-reading): theigors/rules/coding

This node is the check shape: /review Mode A reads the YAML above
at ticket filing time and verifies tickets positively against it.
When editing behavior, edit the narrative at theigors/rules/coding first,
then reflect the change here.

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)


## Pointers

- **narrative:** `theigors/rules/coding`
- **parent:** `theigors/rules/ticket_design_checks`
- **decision:** `D-scaffold-not-correct-2026-04-21`
