---
name: database decision gate
description: Akien's reason for obsessing over DB metrics — must have clean data before deciding whether to switch DBs for any part of the system
type: project
---

The slow query work and db_proxy metrics collection are not just performance optimization. They are the evidence base for a database migration decision.

**Why:** Before switching any part of the stack away from SQLite (e.g. memories table → Postgres, TWM → Redis, word_graph → DuckDB), Akien needs clean p50/p95/p99 per query pattern showing which bottlenecks are:
- "bad query" — fixable in SQLite (wrong index, SELECT *, missing cache)
- "SQLite fundamental limit" — can't be fixed (write lock contention, no server-side execution, full-table scans at scale)

**How to apply:** When working on any DB query fix or slow query investigation, frame the outcome as: did we fix the query, or did we reveal a SQLite limit? Log the conclusion in the fix. The goal is a clean dataset that lets Akien make the migration call with confidence, not a series of one-off patches.
