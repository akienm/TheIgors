# Cognition module audit — latest classification

**Path:** `theigors/audits/cognition_module_audit/latest`
**Updated:** 2026-04-29T19:30:00Z by cc

Most recent classification of wild_igor/igor/cognition/*.py modules.

2026-04-29 (T-cognition-module-audit, cognition_module_audit_20260430-003029.md):
- LIVE: 72 modules (imported by main.py / turn_pipeline.py / push_sources.py / brainstem / pe_chain — or transitively)
- EXPERIMENTAL: 17 modules (imported only by tests OR behind a feature flag OR imported only by other cognition outside the LIVE transitive set)
- PLACEHOLDER: 0 modules (essentially-empty / TODO-only / pass-only)
- ORPHAN: 4 modules — removal candidates (verify before deleting):
  * wild_igor/igor/cognition/observer.py (114 LOC, no docstring)
  * wild_igor/igor/cognition/pipeline_manager.py (161 LOC, D096 — older filesystem-based pipeline)
  * wild_igor/igor/cognition/prefrontal_cortex.py (43 LOC, 'Prefrontal Cortex - executive reasoning')
  * wild_igor/igor/cognition/reasoning_cache.py (134 LOC, 'file-backed TTL cache for Ollama NE/reasoning')

Re-run: python3 lab/claudecode/audit_cognition_modules.py
Full report path: lab/claudecode/reports/cognition_module_audit_20260430-003029.md

Note: per ticket scope, this audit produces classifications + palace pointer only. Per-module subsystem_index node creation for the 72 LIVE modules is out-of-scope; deferred. Removal candidates above are surfaced for Akien review — DO NOT auto-delete.

Filed/closed: T-cognition-module-audit (2026-04-29)
