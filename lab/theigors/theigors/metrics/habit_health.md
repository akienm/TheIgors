# Habit health — day-close-audit habit health score

**Path:** `theigors/metrics/habit_health`
**Updated:** 2026-04-21 by T-slow-metrics-sensor-tree-pattern

Tracks the habit-health score produced by /day-close-audit. Currently placeholder — day-close-audit surfaces the score in its output but doesn't write it here yet. Consumer: /day-close-audit's final step should increment `samples` and append history when the pattern is adopted there.

Counters:
- `samples` — number of day-close-audits that contributed.
- `latest_score` — most recent score (0-100 integer).
- `history` — one row per day-close-audit run.

Pattern adoption is incremental — day-close-audit touches this subtree when it next gets touched for other reasons. This ticket creates the subtree; wiring is a separate, small, on-touch follow-up.

revision: 2026-04-21 — initial placeholder (T-slow-metrics-sensor-tree-pattern)

