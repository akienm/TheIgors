# new MemoryType variant → tag on existing type

**Path:** `theigors/rules/preferred_paths/new-memory-type`
**Updated:** 2026-04-29 by cc-sprint

applies_when: plan or diff adds a new MemoryType enum variant or equivalent constant
deprecated: new MemoryType enum value
preferred: metadata tag on an existing MemoryType (e.g. FACTUAL + {"tag": "experiment_result"})
why: every new MemoryType requires schema migration, cortex path updates, and test fixture expansion; a metadata tag achieves the same retrieval distinction with no schema change
