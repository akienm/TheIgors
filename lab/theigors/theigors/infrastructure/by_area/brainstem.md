# Brainstem area — infrastructure brief

**Path:** `theigors/infrastructure/by_area/brainstem`
**Updated:** 2026-04-29 by cc-sprint

area: brainstem
primary_files: wild_igor/igor/brainstem/
base_classes:
  - IgorBase (wild_igor/igor/brainstem/igor_base.py) — all classes inherit this
mcp_tools: none direct (brainstem is the runtime host)
proxies:
  - make_home_proxy(), make_local_proxy() (brainstem initializes both)
imap_buses: IMAP bus integration lives in network layer
channels: none (brainstem is upstream of channel)
notes: HIGHEST inertia area. core_patterns.py and main.py require Akien review + audit-design pre-approval before any structural change. Scheduler, habit dispatcher, and TWM trigger logic all live here.
