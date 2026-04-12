# Memory Discipline

**Path:** `theigors/rules/memory-discipline`
**Updated:** 2026-04-12T15:55:13.184913+00:00 by seed_memory_palace

Verify before trusting memory: grep the code, don't trust 'X was removed' claims from prior sessions. Check boot timestamp before claiming code is stale. Use MCP tools (mcp__igor__memory_get/search) not raw psql for memory queries.

## Pointers

- **tool:** `mcp__igor__memory_search`
- **tool:** `mcp__igor__memory_get`
