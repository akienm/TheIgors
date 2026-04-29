# reading_worker_pool — [PLACEHOLDER] Stream-of-blocks queue + local/cloud workers for the rea

**Path:** `theigors/subsystem_index/reading_worker_pool`
**Updated:** 2026-04-27 by cap-map-followups

[PLACEHOLDER] Stream-of-blocks queue + local/cloud workers for the reading-list re-run. Not yet built.

Primary file: (not yet established — docstring to be written when sprint starts)

DISTINCT FROM the live reading subsystem (theigors/subsystem_index/reading), which IS shipping today via wild_igor/igor/tools/reading_engine.py + chunker.py + reading_indexer.py + ebook_reader.py. IGOR_READING_EXTRACT=true gates the live single-extractor path; this worker_pool is a future architecture for parallelized re-run, not the current production path.

When confused: "is reading working?" → yes, see /reading. "Is the worker pool working?" → no, see this node.

Originating tickets: T-reading-audit-qwen-complete (pending, M) — pipeline review feeds this design.
