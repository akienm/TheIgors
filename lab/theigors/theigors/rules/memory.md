# Memory — verify, delegate, persist in tickets

**Path:** `theigors/rules/memory`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Verify before trusting — for memory claims ('X was removed', 'this is stale', etc.), grep the code or check Igor's boot timestamp. Akien restarts often.

Read Igor state via `mcp__igor__channel_read` or the dashboard — process-level greps miss tmux-hosted instances.

Memory shape is tags on existing types — add tags, not new types (effective 2026-04-14). Opportunistic conversion on code touch.

Persist decisions in tickets or slate discussion. `decisions_log.dsb` is generated; direct writes land in the generator's echo, not in durable state.

Delegate research and exploration to Igor: 'investigate X' / 'audit Y' / 'homogenize Z' → Igor runs it, CC reads the output. Token cost + self-understanding.

Session-wrap phrasing: emit exactly `please slash compact preserve:<preserve string>` — no variants.

Compact preserve is a pointer, not a copy: session id + slate path + in-flight hypothesis + surprises that aren't on disk. Duplicating slate/git/DB content into the preserve string rots fast.

revision: 2026-04-21 — reframed to approach-target (T-audit-cc-rules-approach-frame)


## Pointers

- **check:** `theigors/rules/ticket_design_checks/no-new-memory-schemas`
