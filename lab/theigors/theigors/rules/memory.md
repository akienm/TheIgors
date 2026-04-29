# Memory — verify, delegate, persist in tickets

**Path:** `theigors/rules/memory`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Always verify before trusting — for memory claims ("X was removed", "this is stale", etc.), grep the code or check Igor's boot timestamp. Akien restarts often; CC's memory of prior state can lag real state.

Always read Igor state via `mcp__igor__channel_read` or the dashboard — process-level greps miss tmux-hosted instances.

Always shape new memory distinctions as tags on existing types — add tags, never new types (effective 2026-04-14). Opportunistic conversion on code touch.

Always persist decisions in tickets or slate discussion. `decisions_log.dsb` is generated — direct writes land in the generator's echo, not in durable state.

Always delegate research and exploration to Igor: "investigate X" / "audit Y" / "homogenize Z" → Igor runs it, CC reads the output. Token cost + self-understanding both favor this path.

Session-wrap phrasing: always emit exactly `please slash compact preserve:<preserve string>` — no variants.

Compact preserve is always a pointer, not a copy: session id + slate path + in-flight hypothesis + surprises not on disk. Duplicating slate/git/DB content into the preserve string rots fast.

revision: 2026-04-24 — binding-imperative pass (T-directed-positive-prompts-pass-1)

## Pointers

- **check:** `theigors/rules/ticket_design_checks/no-new-memory-schemas`
