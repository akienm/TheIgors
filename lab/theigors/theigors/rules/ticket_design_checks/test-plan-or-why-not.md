# test-plan-or-why-not — ticket declares tests or justifies absence

**Path:** `theigors/rules/ticket_design_checks/test-plan-or-why-not`
**Updated:** 2026-04-21T19:42:54.171707+00:00 by T-palace-ticket-design-rules

applies_when: |
  ticket is not pure documentation, config, or palace data entry.
check_body: |
  ticket declares a test_plan (new tests, affected regressions,
  real-DB integration if applicable) OR explicitly states why
  no tests are needed. Integration tests hit real Postgres.
failure_message: |
  Ticket needs a test_plan: [list tests] OR explicit
  'no tests because: [reason]'. Integration tests hit real DB,
  never mocks. See theigors/rules/coding.

Narrative source (human-reading): theigors/rules/coding

This node is the check shape: /review Mode A reads the YAML above
at ticket filing time and verifies tickets positively against it.
When editing behavior, edit the narrative at theigors/rules/coding first,
then reflect the change here.


## Pointers

- **narrative:** `theigors/rules/coding`
- **parent:** `theigors/rules/ticket_design_checks`
- **decision:** `D-scaffold-not-correct-2026-04-21`
