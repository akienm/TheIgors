# no-sqlite — data persistence must name the Postgres table

**Path:** `theigors/rules/ticket_design_checks/no-sqlite`
**Updated:** 2026-04-21 by T-palace-rules-versioned

applies_when: |
  always. this check fires on every ticket, unconditionally.
  cost is zero when the ticket has nothing to do with persistence.
verdict: DISCARD
check_body: |
  (1) Red-flag scan — judge INTENT, not surface text. The ticket MUST NOT
      PROPOSE any of these (case-insensitive) as a backend, storage mechanism,
      or fallback. Negation constructions ("no sqlite", "without sqlite",
      "Postgres only, no fallback") are expected and pass — they confirm the
      rule. Judge whether SQLite/fallback is being proposed, not just mentioned.

      Red flags (used as proposals, not as prohibitions):
        sqlite, sqlite3, .sqlite, .db as a file store,
        "embedded db", "local db", "file-backed cache", "on-disk cache",
        "both supported", "fallback to postgres", "postgres fallback",
        "sqlite fallback", "dual backend", "dual store", "dual path".

      If any red flag is PROPOSED (not prohibited) → DISCARD with failure_message.

  (2) Positive requirement — if the ticket touches persistence (writes/reads
      state, uses a queue, cache, log, registry, history, counter, shelf, store,
      ledger, or anything that survives a process restart), the ticket MUST name
      the Postgres table(s) it uses. Existing tables preferred; new tables
      require a schema migration note.

  (3) Opt-out — if the ticket does not touch persistence at all, it MUST state
      "no persistence" explicitly in the Design rules section. Silence on the
      topic is not acceptable — the check requires a positive statement either
      way.
failure_message: |
  NO SQLite anywhere. No fallbacks, no dual paths, no "both supported."
  Postgres only. Matched red flag: "<matched phrase>".
  If this ticket does not touch persistence, say so explicitly ("no persistence")
  in the Design rules section. If it does, name the Postgres table.
  See theigors/rules/database.

Narrative source (human-reading): theigors/rules/database

This node is the check shape: /review Mode A reads the YAML above at ticket
filing time and verifies tickets against it. When editing behavior, edit the
narrative at theigors/rules/database first, then reflect the change here.

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)


## Pointers

- **narrative:** `theigors/rules/database`
- **parent:** `theigors/rules/ticket_design_checks`
- **decision:** `D-scaffold-not-correct-2026-04-21`
