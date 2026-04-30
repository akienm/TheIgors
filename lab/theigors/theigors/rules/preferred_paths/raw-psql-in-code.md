# raw psql in code → memory_get / memory_search MCP tools

**Path:** `theigors/rules/preferred_paths/raw-psql-in-code`
**Updated:** 2026-04-29 by cc-sprint

applies_when: any plan or diff writes raw psql or psycopg2 queries against memory_palace inside wild_igor/ or lab/
deprecated: "raw psql" / "psycopg2.connect" for palace reads or writes
preferred: memory_get(path=...) or memory_search(query=...) MCP tool calls
why: MCP tools respect instance routing, caching, and TTL; raw psql bypasses all three and produces hard-coded DB URLs that break on migration
