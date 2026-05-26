# D-rack-diagnostic-trace-2026-05-25
**title:** Add trace_record()/debug_mode to DiagnosticBase; collapse /debug-pe-chain + /igor-diagnose + /cognition-debug into one /diagnose skill
**date:** 2026-05-25
**status:** open
**spawned_tickets:** T-diagnosticbase-trace, T-diagnose-skill, T-consequence-rack-diagnostic-trace

## Decision narrative
DiagnosticBase already has a tagged logger and dump(). Add structured trace_record(event, data) and debug_mode flag so every rack device gets queryable trace history out of the box. Then create a single /diagnose <device> skill that works for any device — surfaces last_traces(), categorizes the issue (code bug / state corruption / external noise), and suggests one fix. Retire /debug-pe-chain, /igor-diagnose, and /cognition-debug as DEPRECATED stubs pointing to /diagnose. Alternative considered: keep separate per-device debug skills (chose collapse because the shim-level trace makes per-device skills redundant and the single surface is simpler to reach for).

## Hypothesis
DiagnosticBase.trace_record() exists; `/diagnose igor` surfaces recent traces for any rack device; /debug-pe-chain shows a DEPRECATED header pointing to /diagnose.

## Measurement Signal
`from diagnostic_base.base import DiagnosticBase; DiagnosticBase('test').trace_record('e')` runs without error; ~/.claude/skills/debug-pe-chain/SKILL.md starts with DEPRECATED; ~/.claude/skills/diagnose/SKILL.md exists with device-agnostic Steps 1-3.

## Goal Link
none: observability infrastructure — enables diagnosis for any future rack device without per-device skill work.
