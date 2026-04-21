# Database — Postgres everywhere, db_proxy always

**Path:** `theigors/rules/database`
**Updated:** 2026-04-21 by T-palace-rules-versioned

Database rules:
- NO SQLITE ANYWHERE. No fallbacks. No dual-path branches. No "both supported."
  Every code path assumes Postgres. Fallback-shaped language in a ticket
  (e.g. "sqlite fallback", "both supported", "if sqlite else postgres") →
  DISCARD at filing time by theigors/rules/ticket_design_checks/no-sqlite.
- Red flags that mean DISCARD at ticket-filing time:
    sqlite, sqlite3, .sqlite, .db (as an embedded file store),
    "embedded db", "local db", "file-backed cache", "on-disk cache",
    "both supported", "fallback to postgres", "sqlite fallback",
    "dual backend", "dual store", "dual path".
- db_proxy does blanket `?→%s` translation — use `jsonb_exists(metadata, 'key')`
  not `metadata ? 'key'`.
- All DB access through db_proxy, never raw psycopg2 in tools.
- Primary DB: Igor-wild-0001 at 127.0.0.1.
  Runtime dir: ~/.TheIgors/Igor-wild-0001/ (capital I).

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)


## Pointers

- **check:** `theigors/rules/ticket_design_checks/no-sqlite`
