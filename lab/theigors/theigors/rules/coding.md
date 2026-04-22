# Coding — read first, respect inertia

**Path:** `theigors/rules/coding`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Before editing, read the file and check its inertia level — your edit fits one of three shapes.

Inertia tiers:
- HIGH (≥0.90): brainstem/, memory/models.py, cognition/reasoners/base.py. Edit with strong justification, discuss at the plan stage, CC holds the diff.
- MEDIUM: cognition/, memory/cortex.py, main.py. Discuss the shape first; Igor or CC can author.
- LOW: tools/, dashboard/, word_graph.py. Freely improvable; Igor authors by default.

HIGH-inertia work stays with CC; Igor handles everything else.

revision: 2026-04-21 — reframed to approach-target (T-audit-cc-rules-approach-frame)


## Pointers

- **check:** `theigors/rules/ticket_design_checks/oop-first`
- **check:** `theigors/rules/ticket_design_checks/test-plan-or-why-not`
