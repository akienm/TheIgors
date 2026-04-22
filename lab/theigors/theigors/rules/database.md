# Database — Postgres everywhere, db_proxy always

**Path:** `theigors/rules/database`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Every code path assumes Postgres, through `db_proxy`, on `Igor-wild-0001` at 127.0.0.1. Runtime dir: `~/.TheIgors/Igor-wild-0001/` (capital I).

Use `jsonb_exists(metadata, 'key')` — db_proxy's blanket `?→%s` translation eats `metadata ? 'key'`.

Protecting the Postgres-only path (constraints checked at ticket-filing time by `theigors/rules/ticket_design_checks/no-sqlite`, verdict DISCARD if any of these are proposed as backend, storage, or fallback):
    sqlite, sqlite3, .sqlite, .db (as an embedded file store),
    "embedded db", "local db", "file-backed cache", "on-disk cache",
    "both supported", "fallback to postgres", "sqlite fallback",
    "dual backend", "dual store", "dual path".
Negation constructions ("no sqlite", "without sqlite") pass — they confirm the rule.

Preserve the live DB: `~/.TheIgors/Igor-wild-0001/wild-0001.db` is the instance's live state. Delete or reset needs explicit Akien approval.

revision: 2026-04-21 — reframed to approach-target (T-audit-cc-rules-approach-frame)


## Pointers

- **check:** `theigors/rules/ticket_design_checks/no-sqlite`
