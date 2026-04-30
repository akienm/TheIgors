# Reasoning area — infrastructure brief

**Path:** `theigors/infrastructure/by_area/reasoning`
**Updated:** 2026-04-29 by cc-sprint

area: reasoning
primary_files: wild_igor/igor/cognition/reasoners/
base_classes:
  - IgorBase (wild_igor/igor/brainstem/igor_base.py)
  - ReasonerBase (wild_igor/igor/cognition/reasoners/base.py)
mcp_tools:
  - memory_get, memory_search
  - hot_attractors, wg_neighbors (word-graph proximity)
proxies:
  - make_home_proxy() for salience writes
imap_buses: none active in this area
channels: none direct
notes: pe_chain.py is the primary coordinator — new reasoners subclass ReasonerBase and register in pe_chain STAGE registry. HIGH-inertia: base.py and pe_chain.py require Akien review before structural changes.
