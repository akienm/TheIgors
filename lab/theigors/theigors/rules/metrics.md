# Metrics — slow progress counters live in SensorTree palace subtrees

**Path:** `theigors/rules/metrics`
**Updated:** 2026-04-21 by T-slow-metrics-sensor-tree-pattern

Slow progress metrics (counts + history that a human would read once a week) live in palace subtrees under `theigors/metrics/`. High-frequency instrumentation stays in existing stores (`clan.metrics`, observability tables) — this pattern is for the weekly-read shape.

Frequency heuristic:
- If the number updates faster than once per sprint → clan.metrics / logs.
- If the number tells a weekly story about progress → SensorTree palace subtree.

Shape per metric (modelled on `theigors/metrics/approach_frame_audit/`):
- One counter node per tracked value (content is the integer).
- Optional derived nodes (e.g. `pct_complete`).
- One `history` node (append-only rows, `YYYY-MM-DD HH:MM | key:N key:N`).

Backing helpers (one import, reusable): `wild_igor.igor.tools.palace_metric` exposes `read_counter`, `increment_metric`, `append_history`, `parse_history`, `render_sparkline`, `render_history_sparkline`.

Reference implementation: `theigors/metrics/approach_frame_audit/` — shipped by T-approach-frame-sensor-node (2026-04-21).

Example subtrees:
- `theigors/metrics/pass2_findings/` — Pass-2 audit epic progress (filed/resolved counters).
- `theigors/metrics/habit_health/` — day-close-audit habit health score.

revision: 2026-04-21 — initial (T-slow-metrics-sensor-tree-pattern)

