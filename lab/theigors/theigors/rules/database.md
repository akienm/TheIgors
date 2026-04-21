# Database — Postgres everywhere, db_proxy always

**Path:** `theigors/rules/database`
**Updated:** 2026-04-21T19:42:54.171707+00:00 by T-palace-ticket-design-rules

Database rules:
- NO SQLITE ANYWHERE. Everything Postgres.
- db_proxy does blanket `?→%s` translation — use `jsonb_exists(metadata, 'key')` not `metadata ? 'key'`.
- All DB access through db_proxy, never raw psycopg2 in tools.
- Primary DB: Igor-wild-0001 at 127.0.0.1. Runtime dir: ~/.TheIgors/Igor-wild-0001/ (capital I).

## Pointers

- **check:** `theigors/rules/ticket_design_checks/no-sqlite`
