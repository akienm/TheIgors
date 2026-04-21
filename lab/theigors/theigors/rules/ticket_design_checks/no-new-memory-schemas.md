# no-new-memory-schemas — reuse clan.memories / memory_palace

**Path:** `theigors/rules/ticket_design_checks/no-new-memory-schemas`
**Updated:** 2026-04-21T19:42:54.171707+00:00 by T-palace-ticket-design-rules

applies_when: |
  ticket mentions memory, clan.memories, memory_palace, memory
  types, or memory tags.
check_body: |
  ticket uses the existing clan.memories or memory_palace schemas.
  type-shaped distinctions become metadata tags, not new types.
  no new memory tables proposed.
failure_message: |
  Memory tickets reuse clan.memories / memory_palace. Type
  distinctions go in tags, not new types (rule since 2026-04-14).
  See theigors/rules/memory.

Narrative source (human-reading): theigors/rules/memory

This node is the check shape: /review Mode A reads the YAML above
at ticket filing time and verifies tickets positively against it.
When editing behavior, edit the narrative at theigors/rules/memory first,
then reflect the change here.


## Pointers

- **narrative:** `theigors/rules/memory`
- **parent:** `theigors/rules/ticket_design_checks`
- **decision:** `D-scaffold-not-correct-2026-04-21`
