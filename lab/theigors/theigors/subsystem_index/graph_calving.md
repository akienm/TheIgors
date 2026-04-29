# graph_calving — Memory-tree splitting when subtrees grow too large/deep

**Path:** `theigors/subsystem_index/graph_calving`
**Updated:** 2026-04-27 by cap-map-followups

Graph calving: when a memory tree exceeds size or depth thresholds, calve a subtree into a new tree (reparent its root, update facia + tree_index for both sides). Detection is live; execution is partial.

Live today:
  - Calving candidate detection (depth-based scan)
  - On-write trigger check (cortex._maybe_calve at write path)
  - Attractor scoring + orphan adoption (related: IGOR_NODE_ADOPTION_ENABLED)
  - Protected nodes: ROOT, CP1-CP6, ID1-ID14 — never calved from parent.

Not yet built:
  - Actual split operation (T-calving-split-op pending)
  - Post-calve cleanup of facia + tree_index (T-calving-post-cleanup pending)
  - Trigger-on-write threshold of 1000 nodes (T-calving-trigger-on-write pending)
  - Epic: T-graph-calving-execution (split trees, not just detect candidates).

Primary files: wild_igor/igor/memory/cortex.py (T-graph-calving section ~line 5502+, _maybe_calve at line 1517), wild_igor/igor/tools/graph_ops.py (run_calving_check + node adoption tools).

Also see: wild_igor/igor/memory/node_id.py (serial-calving counter for ID uniqueness — distinct from graph calving but related naming).

Gates: IGOR_CALVING_ENABLED=true (currently true) — enables candidate scan; IGOR_NODE_ADOPTION_ENABLED=true — enables orphan adoption.

Shaped by decisions: D153 (graph-calving-design).
