# Per-audit model routing table

**Path:** `theigors/audits/model_routing`
**Updated:** 2026-04-29 by cc-sprint

Each audit skill declares its model in SKILL.md frontmatter. This table is the canonical source.

audit-design:   opus    — broadest design reasoning; runs at /decided
audit-ticket:   haiku   — declarative checklist, low reasoning load
audit-precode:  haiku   — path+symbol verification; escalate to sonnet when HIGH-inertia in plan
audit-smell:    sonnet  — code quality judgment, fix-one-leave-many detection
audit-debris:   haiku   — mechanical cleanup checks
audit-day:      sonnet  — cross-day consistency + watch-for pattern matching
audit-expert:   opus    — per-expert broadest lens; one expert per run
audit-audits:   sonnet  — weekly cadence; opus — monthly deep-dive

Constraint: when Sonnet is driving the session, audit-design and audit-expert still escalate to Opus.
Cost tracking: audit_telemetry.emit_run_record() includes model field per run.
