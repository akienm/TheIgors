# Memory discipline — verify, don't trust prior claims

**Path:** `theigors/rules/memory`
**Updated:** 2026-04-20T20:22:35Z by migrate_rules_to_palace.py

Memory hygiene:
- Verify before trusting memory. Don't trust 'X was removed' claims from prior sessions — grep the code.
- Check Igor boot timestamp before claiming code is stale (Akien restarts frequently).
- Never grep for Igor process — use `mcp__igor__channel_read` or the dashboard.
- NO new memory types, tags only (as of 2026-04-14). Type-shaped distinctions become metadata tags. Opportunistic conversion on code touch.
- NEVER write to decisions_log.dsb. Persistence is tickets OR slate discussion, nothing else.
- DELEGATE research/exploration to Igor. 'Investigate X' / 'audit Y' / 'homogenize Z' → Igor does it, not CC. Token cost + self-understanding.
- Session-wrap phrasing: at session-boundary moments, emit exactly `please slash compact preserve:<preserve string>` — no variants.
- Compact preserve is a POINTER, not a copy. Only include what's NOT recoverable from slate/git/DB (session id, slate pointer, in-flight hypothesis, rules surfaced this run, non-slate surprises).
