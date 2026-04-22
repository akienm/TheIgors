# D-sqlite-removal-2026-04-22

**Summary:** SQLite rule was "stated but never enforced." Pass-2 audit Gap 1 (severity high) flagged `make_home_proxy` SQLite fallback weeks ago; it sat dead in markdown until re-discovered today via slow-query log. Reshape: kill SQLite entirely (including tests), enforce via CI grep-check, and build a mechanism so audit findings don't sit dead again.

**Context:** Discovered during D-slow-query-triage sprint — T-scope-backfill-migration-loop surfaced that SQLite code paths still exist in `make_home_proxy` and `cortex._init_db()` even though the "no SQLite anywhere" rule has been in CLAUDE.md/palace for weeks. Tests used the fallback for isolation, keeping the code alive. Testing moves to a dedicated Postgres schema with per-session drop; SQLite removal completes.

**Spawned tickets:**
- T-test-postgres-schema (M, priority 0.85) — unblocks removal
- T-remove-sqlite-fallback (L, priority 0.80, gated on T-test-postgres-schema)
- T-no-sqlite-enforcement (S, priority 0.75) — CI grep-check, soft → hard
- T-audit-findings-to-tickets (M, priority 0.65) — no more dead-markdown findings

**Supersedes:** T-scope-backfill-migration-loop (Postgres gate already shipped 2026-04-17; SQLite path being removed entirely makes the gate-fix moot).

**Pre-approvals (HIGH-inertia touches):** db_proxy.py + cortex.py, 2026-04-22, reason: audit finding + kill-SQLite rule enforcement.

**Date:** 2026-04-22
**Status:** open
