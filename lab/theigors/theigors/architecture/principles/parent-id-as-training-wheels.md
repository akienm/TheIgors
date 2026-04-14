# parent_id as training wheels

**Path:** `theigors/architecture/principles/parent-id-as-training-wheels`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

The parent_id field on a memory is a one-tree-per-node simplification — training wheels for the case when a node has obvious primary parentage. Real tree membership is plural — nodes belong to many trees via interpretive_edges. Activation trails (tails) record which tree's traversal reached a node THIS time, so the active parent is contextual, not stored. DON'T be tempted to widen parent_id into a list when a node accumulates multiple parents — use interpretive_edges.

From D155 (now T-architecture-core-principles 2026-04-14).

## Pointers

- `wild_igor/igor/memory/models.py`
- `wild_igor/igor/memory/cortex.py`
