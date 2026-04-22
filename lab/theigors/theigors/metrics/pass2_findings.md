# Pass-2 findings — epic progress tracker

**Path:** `theigors/metrics/pass2_findings`
**Updated:** 2026-04-21 by T-slow-metrics-sensor-tree-pattern

Tracks T-epic-fix-all-pass2-findings progress. ~154 proposed findings from pass2_output/area_*.md; each becomes a child ticket filed via /decided per area.

Counters:
- `filed` — children filed so far (starts at a few already-filed).
- `resolved` — children shipped or discarded with rationale.
- `outstanding` — derived = proposed - resolved.
- `history` — batch updates on filing + close events.

Expected consumer: a periodic ticket-state query that reads `cc_queue.list`, counts by `epic: T-epic-fix-all-pass2-findings` tag, increments counters + appends history. Update logic lives in whatever script runs at /day-close or per-filing time.

revision: 2026-04-21 — initial subtree (T-slow-metrics-sensor-tree-pattern)

