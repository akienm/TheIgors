# D-sqlite-migration-phase-bc-2026-05-05
**title:** Migrate all SQLite-ism callers to native Postgres SQL and delete the db_proxy shim
**date:** 2026-05-05
**status:** open
**spawned_tickets:** T-sqlite-out-main-pragma, T-sqlite-out-small-callers, T-sqlite-out-word-graph, T-sqlite-out-cortex, T-db-proxy-shim-delete

## Decision narrative
Phase A inventory (T-db-proxy-sqlite-shim-retire) confirmed 6 files use db_proxy's SQLite-compat translation layer. This decision covers the full migration: all callers switch to native Postgres SQL (ON CONFLICT, strpos, %s, RETURNING id), then the shim classes are deleted from db_proxy.py. cortex.py is HIGH-inertia and requires Akien pre-approval before sprinting. See Phase A inventory at lab/design_docs/db-proxy-sqlite-callsites-20260505.md.
