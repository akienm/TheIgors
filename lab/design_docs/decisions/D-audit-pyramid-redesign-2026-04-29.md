# D-audit-pyramid-redesign-2026-04-29
**title:** Restructure audit infrastructure to constrain Sonnet's failure modes — unified audit-<scope> family + meta-audit + Sonnet-mistakes-as-rules
**date:** 2026-04-29
**status:** open
**spawned_tickets:** T-audit-rename-pyramid, T-audit-telemetry-shape, T-rule-inherit-base-class, T-rule-preferred-paths-seed, T-rule-preferred-paths-code-scan, T-audit-design-skill, T-audit-ticket-skill, T-audit-precode-skill, T-audit-smell-skill, T-audit-debris-skill, T-audit-day-skill, T-audit-expert-skill, T-audit-audits-skill, T-sprint-infrastructure-brief, T-audit-model-routing, T-auto-scan-for-rest-tickets, T-map-igor-skill, T-detailed-logging-audit

## Decision narrative

The existing audit/review/cleanup skills accumulated organically; some overlapped, some had narrow scope ("mainly look at X"), and the pyramid had gaps (no precode-time check, no meta-audit). This decision restructures the audit infrastructure into a unified `audit-<scope>` family with explicit responsibilities per layer, codifies Sonnet's known failure modes as palace rules and audit checks (so Akien can shift toward pure architecture work), and adds a meta-audit that consumes structured telemetry from every layer to optimize the audit process itself without re-reading the codebase.

### Pyramid shape (renamed + extended)

| Layer | When | Model |
|---|---|---|
| audit-design | called by /decided | Opus |
| audit-ticket | per-ticket draft | Haiku |
| audit-precode (NEW) | between /sprint plan and first edit | Haiku → Sonnet on HIGH-inertia |
| audit-smell (NEW) | post-code, pre-test | Sonnet |
| audit-debris | post-test, pre-commit (folds /validate-files) | Haiku |
| audit-day | end-of-day | Sonnet |
| audit-expert | weekly rotation / monthly full / on-demand | Opus per expert |
| audit-audits (NEW) | weekly meta over telemetry | Sonnet weekly, Opus monthly |

Two Opus seats: design audit and expert panel. Both low-volume, high-leverage, and exactly the work where Sonnet drives Akien to drive *it*.

### Sonnet failure modes as first-class checks

1. **Fix-one-leave-many** — audit-smell walks the call graph on signature changes; audit-day sweeps the day's diffs for partials and auto-drafts scan-for-rest tickets.
2. **Pattern regression / fallback to deprecated paths** — palace rule `theigors/rules/preferred_paths` (declarative `deprecated → preferred` pairs); audit-precode + audit-smell enforce.
3. **Architectural amnesia** — `/sprint` plan-review surfaces a one-screen infrastructure brief from `theigors/infrastructure/by_area/<area>` (positive scaffolding, point-of-use).
4. **Helpful-refactor drift** — audit-smell promotes diff-drift from "finding" to AMEND-by-default. Drift requires explicit ticket extension.

### Logging foundation

Corrected framing (Akien): there is no logger to import. The basemost class IS the logging+introspection layer for both Igor and unseen_university. **Every non-library class inherits from it.** This rule is promoted from informal-and-implicit to first-class palace rule (`theigors/rules/inherit-base-class`) with a corresponding audit-ticket check shape. Detailed single-run logging audit deferred to `T-detailed-logging-audit` (gated until the pyramid restructure ships).

### Telemetry shape

Every audit emits one structured run record per invocation at `theigors/audits/<level>/runs/<timestamp>` (level, ran_at, inputs/checks counts, findings with upstream-layer attribution, duration, tokens, model, watch_next stats). Watch-for notes are first-class palace nodes with TTL.

`audit-audits` is the consumer — recurring smell promotion candidates, upstream-miss accumulation, watch-for ROI, dead-check retirements, false-positive sweeps, cost-per-finding, habit health, cross-layer coherence. No codebase reads at the meta level — the corpus is the telemetry.

### Inspection skill

`/map-igor` (Haiku, on-demand) produces a JSON snapshot of Igor's full state to `~/.TheIgors/maps/igor-map-<timestamp>.json` plus a one-screen stdout summary. Diff mode: `/map-igor --since=yesterday`. Stand-alone, but readable as input by audit-day and audit-audits.

### Open questions resolved by CC

- **Auto-scan-for-rest tickets:** YES (turns the bug pattern into a 24h self-healing loop instead of weeks-late noticing).
- **Preferred-paths seed:** BOTH — initial seed (CC's draft) ships first; code-scan augment runs after to find patterns the manual draft missed.

### Scope
Conversation since context-load (no `/design` marker; treated whole conversation as design block). Scope explicitly does not include retrofitting existing non-inheriting classes — that's a separate ticket once `T-rule-inherit-base-class` ships.

## Rollup

**Closed at:** 2026-04-29T21:21:39.316290+00:00
**Ticket count:** 18 (all closed)

### Shipped via
- T-audit-design-skill (M) — Build audit-design skill — called by /decided  `done` — Built ~/.claude/skills/audit-design/SKILL.md with 9 positive checks (approach-frame goal, runtime-observable success, alternatives, constraints, missing-pass, 30d conflicts, palace-rule conflicts, dec
- T-audit-rename-pyramid (S) — Rename all audit skills to audit-<scope> shape  `done` — pe_chain autonomous: pass
- T-rule-inherit-base-class (S) — Promote inherit-base-class to first-class palace rule  `done` — Promoted to first-class palace rule. Added theigors/rules/inherit-base-class (narrative covering: basemost class IS the logging+introspection layer for both Igor and UnseenUniversity; lineage AgentBas
- T-rule-preferred-paths-seed (S) — Palace rule preferred_paths — initial seed of deprecated→preferred pairs  `done` — Seeded 7 palace nodes: theigors/rules/preferred_paths/* with 6 deprecated→preferred pairs (raw-psql, channel-direct-write, direct-db-write, print-statement, new-memory-type, feature-flag) plus parent 
- T-audit-model-routing (S) — Codify per-audit model routing — Opus at design + expert tiers  `done` — Seeded theigors/audits and theigors/audits/model_routing palace nodes with per-audit model table (opus: design+expert, haiku: ticket+debris+precode, sonnet: smell+day+audits). Existing skill frontmatt
- T-audit-smell-skill (L) — Build audit-smell skill — post-code, pre-test code-quality layer  `done` — Built ~/.claude/skills/audit-smell/SKILL.md describing 17 checks (bare except, silent-return-False, shape-names, dead code, what-comments, mocked DB, speculative flags, new memory tables, SQLite, back
- T-audit-telemetry-shape (M) — Audit telemetry — palace tree + per-run record schema  `done` — Created lab/claudecode/audit_telemetry.py: AuditRunRecord dataclass, emit_run_record() → theigors/audits/<level>/runs/<ts>, emit_watch_next() with TTL, read_runs() + read_watch_next(). Seeded theigors
- T-audit-audits-skill (L) — Build audit-audits skill — meta-audit over all audit telemetry  `done` — Built ~/.claude/skills/audit-audits/SKILL.md describing 8 analyzers (recurring smell promotion, upstream-miss accumulation, watch-for ROI, dead-check retirement, false-positive sweeps, cost-per-findin
- T-sprint-infrastructure-brief (M) — /sprint plan-review — surface infrastructure brief for touched area  `done` — Seeded 8 palace nodes theigors/infrastructure/by_area/{cognition,memory,network,tools,reasoning,brainstem,index,parent}. Created sprint_infrastructure_brief.py (InfrastructureBrief class, area detecti
- T-audit-precode-skill (M) — Build audit-precode skill — between /sprint plan and first edit  `done` — Created ~/.claude/skills/audit-precode/SKILL.md: 7 checks (file existence, symbol grep, HIGH-inertia reaffirmation, preferred-paths, test plan named, docstring plan, diff-size estimate). Model: Haiku.
- T-audit-debris-skill (M) — Build audit-debris (rename + fold validate-files + own docs-update)  `done` — Created ~/.claude/skills/audit-debris/SKILL.md: 10 checks (temp files, runtime staged, .env, debug artifacts, log growth, test DB rows, file placement, docstring rot, subsystem_index, commented code).
- T-audit-day-skill (M) — Extend audit-day — cross-day watch-for + fix-one-leave-many sweep  `done` — Created ~/.claude/skills/audit-day/SKILL.md: inherits day-close-audit + cross-day watch-for, fix-one-leave-many sweep, subsystem_index drift, inertia drift, TWM gaps, habit health, scan-for-rest auto-
- T-audit-ticket-skill (M) — Extend audit-ticket (formerly /review filing-time) — validation/remediation/observability  `done` — Created ~/.claude/skills/audit-ticket/SKILL.md: inherits /review + 7 new checks (validation steps, remediation, rollback for HIGH-inertia, logging requirements, observability assertion, split test, au
- T-auto-scan-for-rest-tickets (S) — audit-day fix-one-leave-many → auto-draft scan-for-rest tickets  `done` — Created lab/claudecode/scan_for_rest_drafter.py: ScanForRestDrafter class drafts fix-one-leave-many scan tickets to /tmp/ with area detection, caller lists, scope boundary. audit-day SKILL.md step 8 c
- T-rule-preferred-paths-code-scan (M) — Augment preferred_paths via scan of recent Sonnet diffs  `done` — Created lab/claudecode/preferred_paths_scan.py: PathScanReport scans 60d git history for 6 deprecated patterns (raw-psql, channel-direct, print, new-MemoryType, feature-flag, direct-db-write). Outputs
- T-map-igor-skill (M) — Build /map-igor skill — Haiku, on-demand JSON snapshot of Igor  `done` — pe_chain autonomous: pass
- T-audit-expert-skill (M) — Rework audit-expert — broadest lens per expert + watch_next emission  `done` — Created ~/.claude/skills/audit-expert/SKILL.md + lab/claudecode/cc_skills/audit-expert/SKILL.md: 11-expert panel (Cognitive Scientist, Systems Architect, Safety, HCI, Distributed Systems, ML Engineer,
- T-detailed-logging-audit (L) — Detailed single-run logging audit (DEFERRED — gated)  `done` — audit_logging.py callsite-level audit shipped (lab/claudecode/audit_logging.py + tests/test_audit_logging.py + lab/claudecode/reports/logging_audit_20260429-211639.md). 456 files, 2522 callsites scann

_Generated by cc_queue.py _decision_rollup. File-stub until T-decisions-into-palace-subtree moves rollups into the memory palace._
