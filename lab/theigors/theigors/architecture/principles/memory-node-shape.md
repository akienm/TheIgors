# memory-node shape

**Path:** `theigors/architecture/principles/memory-node-shape`
**Updated:**  by 

A memory is id + three key/value stacks — not a row of typed columns.

The three stacks:
  1. **metadata** — kind-of-memory, creation date, TTL, test_data, employer_id, scope, display_name, facia_role, etc. Anything that describes the memory.
  2. **triggers** — named handles pointing into payload cells. A memory can have multiple triggers (same as a biological engram). Different triggers activate different payload cells.
  3. **payload** (D260) — combination of data and simple engram-program code. Cells named by triggers.values(). NARRATIVE is the canonical embedding source. Data fields are constants this node brings.

Anything that needs to live with a memory goes into **metadata**, not a new column. The wide "memories" table with columns is a migration artifact being split into many small tables; depending on any specific column name is reaching for something that's going away.

This is the *shape* form of `everything_is_memory`. That principle says all state is a memory; this one says how a memory is shaped.

Anti-pattern: "I need to store X with every memory, let me add a column." Right pattern: "I need to store X with every memory, let me stamp metadata.X at cortex.store()."

From Akien 2026-04-15 during T-test-data-lifecycle scoping — Claude reached for an expires_at column and Akien caught it.

## Pointers

- `lab/design_docs_for_igor/architecture_root.dsb#CORE_PRINCIPLES`
- `lab/design_docs_for_igor/subsystem_memory.dsb`
- `D260`
