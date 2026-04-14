# timestamp ID format uniform

**Path:** `theigors/architecture/principles/timestamp-id-format-uniform`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

Use the D256 timestamp ID format — yyyymmdd.hhmmssuuuuuu.xxxxxxx (date . time-with-microseconds . short-commit-hash) — as the canonical id shape across all node types. Don't introduce parallel id encodings. Already in use by instance_log, GOAL_, PRA_, PR_GOAL_*. The format encodes uniqueness, sort order, age, and provenance in one human-readable string.

From D011 walk 2026-04-14 (base-34 alternative was rejected because the timestamp format already covers everything it would have).

## Pointers

- `wild_igor/igor/tools/instance_tracker.py`
