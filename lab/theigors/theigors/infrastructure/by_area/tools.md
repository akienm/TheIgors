# Tools area — infrastructure brief

**Path:** `theigors/infrastructure/by_area/tools`
**Updated:** 2026-04-29 by cc-sprint

area: tools
primary_files: wild_igor/igor/tools/
base_classes:
  - IgorBase (wild_igor/igor/brainstem/igor_base.py)
  - Tool + registry (wild_igor/igor/tools/registry.py)
mcp_tools:
  - memory_get, memory_search (for palace reads)
  - habit_list (to check registered habits)
proxies:
  - make_home_proxy() for any clan writes
  - _load_ticket() for queue.json reads (preferred over raw file parse)
imap_buses: none active in this area
channels: cc_channel (via _post_to_channel)
notes: every tool must register via registry.register(Tool(...)). No SQLite. No new MemoryType variants.
