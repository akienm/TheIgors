# no-sqlite — data persistence must name the Postgres table

**Path:** `theigors/rules/ticket_design_checks/no-sqlite`
**Updated:** 2026-04-21T19:42:54.171707+00:00 by T-palace-ticket-design-rules

applies_when: |
  ticket description mentions data persistence, storage, records,
  databases, tables, CRUD operations, or writing/reading state.
check_body: |
  ticket names the Postgres table(s) it will use (existing preferred).
  ticket does NOT introduce or mention sqlite.
  for a new table, ticket notes the schema migration required.
failure_message: |
  Data-persistence ticket must name the Postgres table
  (existing preferred; new table requires a migration note).
  No sqlite anywhere. See theigors/rules/database.

Narrative source (human-reading): theigors/rules/database

This node is the check shape: /review Mode A reads the YAML above
at ticket filing time and verifies tickets positively against it.
When editing behavior, edit the narrative at theigors/rules/database first,
then reflect the change here.


## Pointers

- **narrative:** `theigors/rules/database`
- **parent:** `theigors/rules/ticket_design_checks`
- **decision:** `D-scaffold-not-correct-2026-04-21`
