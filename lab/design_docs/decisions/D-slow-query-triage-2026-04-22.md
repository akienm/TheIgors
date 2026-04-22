# D-slow-query-triage-2026-04-22

**Summary:** Igor's DB is drowning in slow queries (55k entries in db_queries.log, 20s preparse on trivial input), blocking the "Igor helps with his own code" goal. Fix the top offenders so Igor can respond conversationally.

**Context:** Discovered during live debug session — boot took 3+ minutes, console input unresponsive, 20s preparse on "hello?". The write-side (db_proxy → db_queries.log) and read-side (analyze_slow_queries tool) infrastructure both exist but findings were never surfaced or acted on. Top offenders: 38k scope-backfill UPDATE loop, 9k _migrations re-checks per session, 891 get_attractors full-table-scans, 5.8s wg_meta upsert worst-case.

**Spawned tickets:**
- T-scope-backfill-migration-loop (M, priority 0.85)
- T-migrations-lookup-cache (S, priority 0.80)
- T-get-attractors-tree-walk (M, priority 0.75)
- T-wg-meta-upsert-latency (M, priority 0.65)
- T-slow-query-boot-surface (S, priority 0.55)

**Date:** 2026-04-22
**Status:** open
