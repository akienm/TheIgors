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

Corrected framing (Akien): there is no logger to import. The basemost class IS the logging+introspection layer for both Igor and agent_datacenter. **Every non-library class inherits from it.** This rule is promoted from informal-and-implicit to first-class palace rule (`theigors/rules/inherit-base-class`) with a corresponding audit-ticket check shape. Detailed single-run logging audit deferred to `T-detailed-logging-audit` (gated until the pyramid restructure ships).

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
