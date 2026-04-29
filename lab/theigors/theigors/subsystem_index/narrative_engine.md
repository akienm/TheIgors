# narrative_engine — Arc / context builder. Pulls from TWM + ring + active goals + milieu. 

**Path:** `theigors/subsystem_index/narrative_engine`
**Updated:** 2026-04-27 by cap-map-followups

Arc / context builder. Pulls from TWM + ring + active goals + milieu. Sleep consolidation lives here (NE._deep_consolidation_pass).

Primary file: wild_igor/igor/cognition/narrative_engine.py — read its top-of-file docstring for the canonical explanation.

Also see: wild_igor/igor/cognition/milieu.py, wild_igor/igor/cognition/thalamus.py

Shaped by decisions: D352, D353

---
INVARIANT (NE/stew threshold coupling, 2026-04-27): NE force-run threshold is 0.6 (narrative_engine.py:477, "salience >= 0.6"). Reading-stew chunks are deposited at salience 0.65 (ebook_reader.py:745) so they reliably trigger force-run. Constraint: stew salience must remain strictly greater than the NE force-run threshold. If either value moves, the other must move with it, or stew chunks stop triggering NE integration. Other 0.65-salience deposits (experiment_outcome, sensor_tree, push_sources, main.py) inherit the same coupling.

## Pointers

- `wild_igor/igor/cognition/narrative_engine.py`
- `wild_igor/igor/cognition/milieu.py`
- `wild_igor/igor/cognition/thalamus.py`
