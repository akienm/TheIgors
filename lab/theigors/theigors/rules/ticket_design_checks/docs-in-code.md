# docs-in-code — load-bearing touch must name its docstring

**Path:** `theigors/rules/ticket_design_checks/docs-in-code`
**Updated:** 2026-04-21 by T-palace-rules-versioned

applies_when: |
  ticket touches a load-bearing subsystem (reading, cortex, NE,
  comms, scope_guard, pe_chain, worker pools, inference gateway)
  or any HIGH / MEDIUM inertia file.
check_body: |
  ticket names the primary file whose top-of-file docstring will
  be created or updated. No DSB/CSB expansion; inline in the code.
failure_message: |
  Load-bearing touch → name the primary file and what its
  docstring will say. Separate DSB/CSB docs are historical logs,
  not source of truth. See theigors/rules/docs-live-in-code.

Narrative source (human-reading): theigors/rules/docs-live-in-code

This node is the check shape: /review Mode A reads the YAML above
at ticket filing time and verifies tickets positively against it.
When editing behavior, edit the narrative at theigors/rules/docs-live-in-code first,
then reflect the change here.

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)


## Pointers

- **narrative:** `theigors/rules/docs-live-in-code`
- **parent:** `theigors/rules/ticket_design_checks`
- **decision:** `D-scaffold-not-correct-2026-04-21`
