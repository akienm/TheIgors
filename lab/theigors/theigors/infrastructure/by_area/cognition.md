# Cognition area — infrastructure brief

**Path:** `theigors/infrastructure/by_area/cognition`
**Updated:** 2026-04-29 by cc-sprint

area: cognition
primary_files: wild_igor/igor/cognition/
base_classes:
  - IgorBase (wild_igor/igor/brainstem/igor_base.py)
  - NarrativeEngine (wild_igor/igor/cognition/narrative_engine.py)
mcp_tools:
  - memory_get, memory_search, memory_list_by_type (palace reads)
  - hot_nodes, tail_heat (salience)
  - traces_get, traces_recent (turn trace)
proxies:
  - make_home_proxy() for clan schema writes
imap_buses: none active in this area
channels: cc_channel (via _post_to_channel)
notes: pe_chain and reasoning are in cognition/reasoners/ — see reasoning brief
