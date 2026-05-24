# Igor — Capability Map

**Purpose**: One page that answers "what does Igor *actually do today*?"
vs "what's *planned*?" vs "what's *known broken*?". Read this before
proposing features. If the code disagrees with this doc, the code wins —
update this doc and move on.

**Last updated**: 2026-05-20
**Owner**: Akien — accept PRs from any session that finds drift.

**How this doc earns its keep**: Sonnet kept proposing files that already
existed and features that already shipped. This doc is the answer to
"is X built?" without re-reading the codebase. Keep it short, keep it
truthful, keep it dated.

---

## Reading order

1. **§1 Live today** — the things Igor genuinely does end-to-end.
2. **§2 Gated off** — switches that are `false` right now (and why).
3. **§3 Aspirational** — placeholders, in-flight tickets, things named-but-not-built.
4. **§4 Known broken** — bugs being actively chased.
5. **§5 Explicit non-capabilities** — things people assume Igor does but doesn't.
6. **§6 Open questions** — gaps this doc surfaced that nobody can confidently answer.

If you only have one minute: read §1 and §5.

---

## §1 — Live today (what Igor actually does)

These are the load-bearing subsystems with running code, exercised on
every boot. Source of truth: `theigors/subsystem_index/*` in the palace.
The list here mirrors palace nodes whose status is **not** marked
`[PLACEHOLDER]`.

### Memory & cognition

- **Cortex** (`memory/cortex.py`) — Postgres long-term memory store. Writes
  `clan.memories` rows with type/inertia/salience/valence; provides graph
  traversal and reconsolidation. Live; this is the primary store.
- **TWM** (`memory/cortex.py` + `twm_observations` table) — Push-only
  observation sandbox with TTL. Things expire if not integrated. Live.
- **Ring memory** (hippocampus) — FIFO buffer of last 50 conversation
  turns. Survives restarts. Live.
- **Narrative Engine** (`cognition/narrative_engine.py`) — Background
  daemon. Reads TWM observations, integrates important ones into LTM.
  Runs ~every 60s. Live.
- **Distillation** (`cognition/distillation.py`) — Background daemon.
  EPISODIC → EXPERIENTIAL clustering (embedding similarity), then
  EXPERIENTIAL → PROCEDURAL graduation at activation_count threshold.
  Runs ~every 2h. Live (psycopg2 placeholder bug fixed 2026-05-06, c0e1d0d6).
- **Word graph** (`memory/` + Redis-backed cache) — Two-tier (words +
  bigrams), used for both parsing and generation. Live.

### Reasoning / inference

- **Inference gateway** (`cognition/inference_gateway.py`) — The single
  entry point. Tier ladder: tier.1 habit → tier.2 local Ollama →
  tier.3/3.5 OR cheap/haiku → tier.4 OR sonnet → tier.5 Anthropic
  (gated off) → tier.6 arbiter (gated off). Live.
- **Local Ollama path** (`cognition/inference_ollama.py`) — Default for
  this host. Cluster router prefers yoga9i/yogai7 by rank.
- **OpenRouter routing** (`cognition/inference_openrouter.py`) — Live.
  Budget-gated by `IGOR_CLOUD_BUDGET_FLOOR_USD=10.00`.
- **Thalamus** (`cognition/thalamus.py`) — Intent classifier. 13 categories
  + complexity signal driving tier-start. Live.

### Habits & autonomous action

- **Basal Ganglia** (`cognition/basal_ganglia.py`) — Parallel habit
  scorer. 132 habits with `code_ref` registered (as of 2026-05-06).
  277 tools registered. Fires habits whose score exceeds threshold. Live.
- **Reactive habits** — Habit fires → Python tool runs → result pushes
  to TWM with short TTL. Live.
- **Threshold habits** — Background condition checks (CPU, time, etc.).
  Live.
- **Milieu** (`cognition/milieu.py`) — 3D emotional state (valence,
  arousal, dominance) shared across instances via JSON. Modulates habit
  threshold and tier escalation. Live.

### Code-change pipeline (pe_chain)

`theigors/subsystem_index/scope_guard_and_pe_chain` — primary file
`tools/pe_chain.py`.

- **Pipeline shape**: goal → pe_entry → claim → read → plan → filter →
  hypothesize → scope_guard → implement → test → close. Live.
- **scope_guard** (`tools/scope_guard.py`) — Blocks HIGH-inertia file
  writes without explicit pre-approval. Live.
- **pe_chain** (`tools/pe_chain.py`) — Orchestrates the whole thing.
  Live. P1 (HIGH-inertia hallucination) fixed 2026-05-06 — see §4.

### Channels / I/O

- **Comms router** (`network/` + palace `theigors/subsystem_index/comms`)
  — Channel routing, message envelopes, transports. Live.
- **Utility Closet web server** — `/api/cc_send` + WebSocket broadcast
  to web clients. Live.
- **File inbox channel** (`network/channels/file_inbox.py`) — Live.
- **Direct URL channel** (`network/channels/direct_url.py`) — Live.
- **CC channel** (cross-machine via Postgres) — Cross-instance message
  passing. Live, used by `/context-load` Step 4.

### Self-modification

- **patch_source_file** — Line-range source replacement with syntax
  check before write. Live; preferred self-edit operation.
- **Inertia gate** (`validate_against_core()`) — Pre-delivery check
  catching self-edits that would violate CP1-CP6. Live.
- **Hot reload** (`reload_module()`) — Reloads a module without
  restarting. HIGH-inertia modules blocked. Live.
- **Auto-commit + push** after successful self-edit. Live.

### Reading pipeline

- **Reading extractor** (`reading/` + `IGOR_READING_EXTRACT=true`) —
  Book/URL fetch → chunk → extract via local qwen or cloud. Live.

### Safety

- **SQLite import guard** (`_sqlite_guard.py`, wired in `__init__.py`) —
  Raises `RuntimeError` on any `sqlite3.connect()` call inside
  `wild_igor/igor/`. Legitimate external-file reads (Calibre, DRM) use
  `real_sqlite3` escape hatch. Shipped 2026-05-06 (eafd8b39).

### Operational / infra

- **DB proxy** (`memory/db_proxy.py`) — Wraps every DB call: timing,
  slow-query log, reconnect-on-failure. Live; all DB access routes here.
- **Forensic logger** (`cognition/forensic_logger.py`) — Per-decision
  audit trail. Live.
- **Worker daemon / foreman** — Picks tickets, drives sprint loop. Live
  but slated for retirement (`T-retire-worker-foreman`).
- **Audit runner** (`lab/claudecode/audit_runner.py`) — Registered audit
  checks. Live.

### Skills (Claude side, not Igor)

These are user-facing slash commands the human collaborator uses:
`/context-load`, `/savestateauto`, `/savestate`, `/day-close`,
`/day-close-audit`, `/sorted`, `/fixit`, `/review`, `/sprint`,
`/sprint-batch`, `/ticket`. Live.

---

## §2 — Gated off (switches `false`)

Source: `~/.TheIgors/Igor-wild-0001/igor.switches.cfg`. As of 2026-05-06:

| Switch | State | Reason |
|---|---|---|
| `IGOR_TIER5_ENABLED` | `false` | Direct Anthropic API calls disabled. Hard rule in CLAUDE.md. |
| `IGOR_ARBITER_ENABLED` | `false` | Human-approval queue subsystem off. |
| `IGOR_TURN_PIPELINE` | `false` | New turn-pipeline path inactive; legacy direct-reasoner still authoritative. Tracked by `T-retire-legacy-direct-reasoner-path`. |
| `IGOR_CONSOLIDATION_BATCH` | `0` (disabled) | akiendelllinux has 15GB RAM; qwen2.5:7b consolidation pass forces heavy swap. Re-enable when yoga9i Ollama is up. |

Notable on:
`IGOR_CLOUD_PROGRAMMING`, `IGOR_NPASS_REPLY`, `IGOR_PURSUITS_ENABLED`,
`IGOR_CALVING_ENABLED`, `IGOR_SELF_EDIT_ENABLED`,
`IGOR_NODE_ADOPTION_ENABLED`, `IGOR_READING_EXTRACT`, `IGOR_HABIT_EXTRACT`,
`IGOR_CLOUD_TRAINING_ENABLED`, `IGOR_CONTEXT_WINNOW`, `IGOR_TWO_PHASE_CALLS`.
`IGOR_MAX_DIFFICULTY=1` — Igor only requests tickets at difficulty ≤1 (Apprentice) from the queue. Added 2026-05-20 (D-target-difficulty-tiers).

Note: `IGOR_SINGLE_TICKET=NONE_BETWEEN_CERT_WALKS` — cert-walk mode. In
autonomous operation this is `NONE_BETWEEN_CERT_WALKS` (passes all
tickets). Set to a specific ticket ID during cc-walk cert runs.

**Rule** (from `feedback_no_speculative_feature_flags.md`): don't gate
new work on `IGOR_*_ENABLED` flags. Build to intent; file a
go-live-when companion ticket if rollout needs staging.

---

## §3 — Aspirational / placeholder

Things named in the palace or queue that are **not** built end-to-end.

### Palace `[PLACEHOLDER]` subsystems

- `theigors/subsystem_index/reading_worker_pool` — stream-of-blocks queue
  + local/cloud workers for reading. Not built.
- `theigors/subsystem_index/sleep_memory_auditor` — chains old reading
  memories as `prior_version_of` new ones. Not built.

### Major sprint-ready (status = `sprint`)

These are designed and ready to claim — not yet built:

- `T-igor-programs-himself` (XL) — Igor completes 10 tickets autonomously.
- `T-capability-extraction-from-igor` (XL) — Epic: move capabilities out of Igor into the datacenter.
- `T-concurrent-ne-spawn` (L) — concurrent Centers-of-Attention.
- `T-sleep-consolidation-honesty` (L) — honest Hebbian sleep pass or retract the claim.
- `T-swarm-via-home-web-server` (M) — unified bus swarm web server.
- `T-uc-gmail-google` (L) — Gmail/Google as UC rack shelf.
- `GH-187` — Igor own GitHub identity.
- `GH-209` — Igor writes tests for its own subsystems.
- `GH-210` — Igor self-directed rollback.
- `GH-241` — BG meta-habits as habit graph tree.
- `GH-287` — Igor spawns background workers + polls via MCP.

### Active projects

- **UnseenUniversity** — portable runtime substrate, live at
  `~/dev/src/UnseenUniversity`. Phase 0 in progress (lab/claudecode
  migration underway, `T-lab-migration-to-agent-datacenter`).

Full list: `python3 ~/TheIgors/lab/claudecode/cc_queue.py list`.

---

## §4 — Known broken

### P1 — pe_chain HIGH-inertia hallucination ✅ FIXED

**Status**: Fixed. Commit 0993b36d (ENGRAM basket isolation — fresh `{}`
per MCPCALL + pre-flight false-fail fixed). Closed 2026-05-06.

~~pe_chain proposes edits to HIGH-inertia files for tickets that don't need
them.~~ Root cause was ENGRAM basket state leaking across concurrent MCPCALL
invocations, causing pre-flight to see stale HIGH-inertia hits.

### Distillation — SQLite placeholder bug ✅ FIXED

**Status**: Fixed 2026-05-06, commit c0e1d0d6. Three queries in
`cognition/distillation.py` used `?` (SQLite) placeholders instead of `%s`
(psycopg2). Were spamming `WARNING bare except` every ~600ms. Now clean.
SQLite guard (eafd8b39) would have caught this at import time.

### Test-suite pre-existing failure

`test_goal_graph.py::test_seed_creates_aspirational_goal` — fails when IMAP
bus is running (port 10143 already in use). Pre-existing; not a regression.

### Latest test run

Most recent `pytest tests/`: **1363 passed, 4 skipped, 1 known failure**.
Run time: ~50s. (Previous 2026-04-27: 3980 passed — count changed due to
test reorganization.)

---

## §5 — Explicit non-capabilities

**Read this before proposing features.** These are the "wait, can Igor
do X?" answers that have tripped sessions in the past.

- ❌ **Igor does not have a "want" primitive.** Goal stack is plumbing
  for pull-that-isn't-there. Anticipation is half-built. See
  `project_missing_want_primitive.md`. Don't assume goal_formation
  works end-to-end.
- ❌ **Igor cannot yet reliably autonomously close tickets end-to-end.**
  pe_chain P1 is fixed, but `T-igor-programs-himself` (XL) has not been
  sprinted. Autonomous ticket processing is sprint-ready but unvalidated.
- ❌ **Tier 5 (direct Anthropic) is off.** Don't propose code paths that
  call Anthropic directly. Use the gateway.
- ❌ **No GPU.** Igor is CPU-only; local inference is Ollama on the
  host's CPU. Don't propose GPU-dependent strategies.
- ❌ **Arbiter (human-approval queue subsystem) is off.** Different from
  ticket-level `approval`. Don't conflate.
- ❌ **No background heartbeat for health checks.** Health is polled on
  demand. Don't propose periodic-heartbeat patterns without reading
  the UnseenUniversity spec first.
- ❌ **No own GitHub identity yet.** `GH-187` (sprint). Igor commits as Akien.
- ❌ **Self-directed rollback not implemented.** `GH-210` (sprint).
  Igor cannot revert its own bad changes today.
- ❌ **Test generation not implemented.** `GH-209` (sprint). Igor does
  not write tests for its own subsystems.
- ❌ **Concurrent Centers-of-Attention (COA) not built.**
  `T-concurrent-ne-spawn` (sprint). NE is single-threaded.
- ❌ **Igor does not write to `decisions_log.dsb` directly.** That's
  a structured echo via `/sorted`. Direct writes corrupt the
  chronological record.
- ❌ **CLAUDE.md is not the canonical rules file.** It's a pre-DB shim.
  Palace `theigors/rules/*` is canonical.

---

## §6 — Open questions (forcing-function output)

These are the "I tried to write authoritative copy and couldn't" gaps.
Each is a candidate ticket or doc fix.

1. **84 modules in `cognition/` — how many are live?** Subsystem index
   names ~10 load-bearing ones. The other ~70+ may be wired in
   transitively, may be experimental, or may be orphans. No quick way
   to tell without dependency analysis. Candidate: orphan-detection
   pass via the day-close audit's Step 10 (already exists; results not
   surfaced here).
2. **132 habits with `code_ref` — how many fire?** `habit health` audit
   step checks for dead `code_ref`s but doesn't surface fire-rate.
   Candidate: per-habit fire counter exposed in `mcp__igor__habit_list`.
3. **The Pursuits subsystem (`IGOR_PURSUITS_ENABLED=true`) is on but
   not in palace's subsystem_index.** Built? Half-built? Where's its
   primary file? Worth a palace node.
4. **Calving (`IGOR_CALVING_ENABLED=true`) — same gap.** No palace
   subsystem entry. What is it, what does it do, what's the primary file?
5. **Reading worker pool is `[PLACEHOLDER]` in palace, but
   `IGOR_READING_EXTRACT=true` is on.** Is reading shipping today or
   not? Where does the gap live?
6. **`turn_pipeline` is gated off but in code (`cognition/turn_pipeline.py`).**
   What's its current completeness? `T-retire-legacy-direct-reasoner-path`
   suggests it's nearly ready but not authoritative. How close?
7. **Igor's voice (`voice_ab.py`) — A/B testing of what?** No palace
   entry. Probably worth one.
8. **NE force-run threshold of 0.6 vs stew salience 0.65** (from glossary)
   — these are tightly coupled; if either changes, the other needs to
   move. Where's that constraint enforced/documented?

---

## How to keep this doc honest

Every `/day-close-audit` should re-verify §1, §2, and §4 against:
- Palace subsystem_index nodes
- `igor.switches.cfg` actual state
- `cc_queue.py list` for in_progress / pending status
- Latest `pytest` summary

When this doc is older than ~7 days, **assume drift**. The fastest way
to catch drift is to grep this doc for any specific claim and verify
it against the named source. The next-fastest way is to add a check to
the audit runner.

---

## Pointers

- **Premise / why this project exists**: `theigors/rules/persona` (palace).
- **Glossary**: `lab/docs/glossary.md`.
- **Architecture (load-bearing subsystems)**: palace
  `theigors/subsystem_index/*`.
- **Programming rules**: palace `theigors/rules/coding`,
  `theigors/rules/commits`, `theigors/rules/database`.
- **Workflow**: palace `theigors/rules/collaboration`, plus skills
  under `~/.claude/skills/`.
- **Decisions**: `lab/design_docs/decisions/` + palace
  `theigors/decisions/*`.
- **Tools registry**: `wild_igor/igor/tools/registry.py`; live count from
  `mcp__igor__habit_list` or registry inspection.
- **MCP tools available to Claude**: `mcp__igor__*`,
  `mcp__igor_akiendell__*`, `mcp__igor_yoga9i__*`,
  `mcp__igor_yogai7__*` — see system tool list.
