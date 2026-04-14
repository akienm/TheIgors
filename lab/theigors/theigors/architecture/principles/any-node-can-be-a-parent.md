# any node can be a parent

**Path:** `theigors/architecture/principles/any-node-can-be-a-parent`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

In the tree-based architecture, any node becomes a parent simply by adding child nodes. Schema doesn't change. If a single datum (a checkbox) needs to become a dropdown list, you tweak metadata and add children. Prefer adding children over widening parent metadata. This is one of the core advantages of the matrix over relational tables.

Surfaced from D124 walk 2026-04-14 — context was hardware inventory where storage might evolve from one disk to many.
