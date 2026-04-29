# Database — Postgres everywhere, db_proxy always

**Path:** `theigors/rules/database`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Always assume Postgres, through `db_proxy`, on `Igor-wild-0001` at 127.0.0.1. Runtime dir: `~/.TheIgors/Igor-wild-0001/` (capital I).

Always use `jsonb_exists(metadata, 'key')` — db_proxy's blanket `?→%s` translation eats `metadata ? 'key'`.

Protecting the Postgres-only path (these constraints check at ticket-filing time via `theigors/rules/ticket_design_checks/postgres-only`, verdict DISCARD when any of these appear as backend, storage, or fallback):
    sqlite, sqlite3, .sqlite, .db (as an embedded file store),
    "embedded db", "local db", "file-backed cache", "on-disk cache",
    "both supported", "fallback to postgres", "sqlite fallback",
    "dual backend", "dual store", "dual path".
Negation constructions ("no sqlite", "without sqlite") always pass — they confirm the rule.

Always protect the live DB: `~/.TheIgors/Igor-wild-0001/wild-0001.db` is the instance's live state. Deletion or reset always needs explicit Akien approval.

revision: 2026-04-24 — binding-imperative pass (T-directed-positive-prompts-pass-1)

## Pointers

- **check:** `theigors/rules/ticket_design_checks/no-sqlite`
