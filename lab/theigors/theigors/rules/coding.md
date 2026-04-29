# Coding — read first, respect inertia

**Path:** `theigors/rules/coding`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Always read the file first and check its inertia level before editing — the edit's shape depends on which tier the file sits in.

Inertia tiers:
- HIGH (≥0.90): brainstem/, memory/models.py, cognition/reasoners/base.py. Always discuss HIGH-inertia edits at plan stage; CC authors the diff with strong justification.
- MEDIUM: cognition/, memory/cortex.py, main.py. Always discuss the shape first; Igor or CC authors.
- LOW: tools/, dashboard/, word_graph.py. Freely improvable; Igor authors by default.

Always keep HIGH-inertia work with CC; Igor handles MEDIUM and LOW.

revision: 2026-04-24 — binding-imperative pass (T-directed-positive-prompts-pass-1)

## Pointers

- **check:** `theigors/rules/ticket_design_checks/oop-first`
- **check:** `theigors/rules/ticket_design_checks/test-plan-or-why-not`
