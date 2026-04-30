# Memory area — infrastructure brief

**Path:** `theigors/infrastructure/by_area/memory`
**Updated:** 2026-04-29 by cc-sprint

area: memory
primary_files: wild_igor/igor/memory/
base_classes:
  - IgorBase (wild_igor/igor/brainstem/igor_base.py)
mcp_tools:
  - memory_get, memory_search (palace reads — preferred over raw psql)
  - memory_list_by_type
proxies:
  - make_home_proxy() — clan schema (memories, memory_palace, ring_memory)
  - Cortex(None) — domain wrapper over home proxy
imap_buses: none active in this area
channels: none
notes: cortex.store() is the preferred write path; direct psycopg2 to memories table is deprecated (see preferred_paths/direct-db-write)
