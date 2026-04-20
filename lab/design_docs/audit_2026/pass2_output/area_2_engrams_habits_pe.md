# Pass 2 deep-dive — Engrams + Habits + pe_chain

Scope: procedural memories (engrams), `payload.cells` + BRANCHIF/EMITIF/FORKIF/
SPAWNIF/MCPCALL, `basal_ganglia.py`, `node_executor.py`, `cursor_runtime.py`,
`pe_chain.py` + pe_* steps, `habit_chunker.py`, `misfire_counter.py`, and
dead-habit code-ref cross-check. Evidence cited to file:line. Disposal call
per-ticket.

## Per-finding verdicts

### Finding P1.1 — silent excepts in `basal_ganglia.select_habit` (persona 1)

- Verdict: **CONFIRMED_WORSE**
- Evidence: `wild_igor/igor/cognition/basal_ganglia.py:854` — the outer
  `except Exception: return (None, 0.0, [])` wrapping the entire
  `select_habit` body. Additionally `basal_ganglia.py:710-714` and
  `:822-826` log via a WARNING but continue — these are only labelled
  `"bare except in ..."`. `:583-584` `_inhibit_neighbors` swallows.
  Five swallowed sites, all in the winner-selection hot path.
- Blast radius: the whole habit selector. A scoring bug — e.g. mangled
  `parsed.intent`, bad `_wg_scores` shape, KeyError in `metadata` — falls
  through and returns `(None, 0.0, [])`. The caller (`main.py`) reads this
  as "no habit won" and silently falls back to LLM. There is no observable
  signal that the selector crashed; turn traces will show `bg_scoring:
  no_candidates_above_threshold` which is indistinguishable from an
  intentional no-match. This is the difference between "basal ganglia
  produced no action" and "basal ganglia crashed and we lied about it."
  Dominance also masks regressions: a bug that kills habit dispatch
  increases tier.2 cost without any alarm.
- Biomimicry: **theatrical**. A real basal ganglia that catastrophically
  failed would produce observable motor symptoms — not silent substitution
  of cortical output. The except-return-default pattern is the opposite
  of "FAIL = Further Advance In Learning" (the in-code joke at the catch
  site). An honest version: catch specific exception classes at known
  failure points; on unknown failure, re-raise with a `log_error`
  `BG_CRASH` forensic entry, and let the caller decide whether to absorb
  via a dedicated recovery path that shows up in turn_trace.
- Proposed ticket:
  - id: T-bg-bare-except-hardening
  - title: Replace bare except in basal_ganglia with typed fail-loud path
  - size: M
  - tags: [cognition, habits, observability, biomimicry]
  - description: The outer `try/except Exception` in `select_habit`
    (basal_ganglia.py:631-855) swallows every non-KeyboardInterrupt error
    and returns a no-winner tuple. Scoring failures become invisible
    "no habits matched" outcomes, hiding regressions behind silent
    tier.2 fallback. Three `bare except in ...` sites (wg scoring,
    inhibition preload, word-graph reinforcement) log WARN-only and
    propagate `None`/`{}` forward; these are the sanest of the lot but
    they also mask root causes.
    Shape of the fix: narrow the outer handler to `KeyboardInterrupt /
    SystemExit / (optional) MemoryError` and let everything else raise
    after a `log_error(kind="BG_CRASH", detail=...)` forensic write +
    TWM marker `bg_error=true`. The three inner sites should keep
    WARN+fallback but MUST also increment a `bg_fallback_counter` tag
    in the turn_trace so health-audit can count them. Add a test that
    injects a deliberate `TypeError` in `_score_habit` and asserts the
    turn_trace carries a `BG_CRASH` entry. Scope: this file only — no
    caller changes. Does NOT change scoring math or gate semantics.
    Not high-inertia (cognition/, not brainstem/).
  - disposal: **SHIP**

### Finding P1.5 — "Hebbian co-activation" is counter increment, not learning (persona 5)

- Verdict: **CONFIRMED_NARROWER** (for this area's slice)
- Evidence: in basal_ganglia's scope the "Hebbian"-adjacent sites are
  `_word_graph.reinforce(winner.id, boost=_boost)`
  (basal_ganglia.py:810) and
  `_word_graph.reinforce_text(...)` upstream. These are scalar increments
  keyed on winner habit ID. Nothing strengthens an edge **between two
  co-activated nodes** at ~ms-ish timescale — the canonical Hebbian
  trigger.
- Blast radius: the word-graph predictor, `#338 surprise scaling`
  (basal_ganglia.py:805-821), and every downstream consumer that believes
  the predictor embodies "wired together". Changing the mechanism would
  ripple into `cortex.spreading_activation`, `hebbian_bridge.py`, and
  the surprise-reward telemetry. But this ticket is about *naming*, not
  mechanism change.
- Biomimicry: **procedural-with-bio-name**. Honest version: rename to
  `co_activation_reinforcer` OR actually wire pairwise edge-strength
  updates into the `interpretive_edges` table on co-activation windows.
  My call: fix the name + docstring NOW, land the mechanism shift as a
  separate deep epic (scope too big for this audit).
- Proposed ticket:
  - id: T-rename-hebbian-to-coactivation-counter
  - title: Rename "Hebbian" sites to co-activation-counter (honesty pass)
  - size: S
  - tags: [docs, biomimicry, naming, low-risk]
  - description: Three files in-area reference "Hebbian" in docstrings
    or comments (basal_ganglia.py top docstring section "means to me",
    hebbian_bridge.py, consolidation.py docstring). None actually perform
    Hebbian pairwise edge-weight adjustment at co-activation timing. The
    mechanism is: increment scalar word/habit weight on winner selection.
    Fix shape: rename the module `hebbian_bridge.py` →
    `coactivation_counter.py` with a one-line back-compat import shim in
    the old path for 2 releases. Update docstrings everywhere to say
    "scalar co-activation counter; NOT Hebbian pairwise edge update —
    see T-true-hebbian-edges for the intended mechanism". File a
    follow-up investigate ticket T-true-hebbian-edges scoped to the
    memory+cortex area (not this area). Does NOT change scoring values,
    word-graph API, or any behavior. Safe to ship immediately; the
    mechanism upgrade is deferred. LOW inertia.
  - disposal: **SHIP**

### Finding P1.6 — "Engram is a single node, not an ensemble" + payload.cells observation + reconsolidation gap (persona 6)

- Verdict: **CONFIRMED_WORSE** (and I found a separate live structural bug
  below — see Gap 1).
- Evidence: `memory/models.py` stores one row per memory. `payload.cells`
  is a list-of-instructions (`wild_igor/igor/cognition/node_executor.py:1-43`
  docstring + the whole executor). Live DB check:
  `SELECT COUNT(*) FROM memories WHERE memory_type='PROCEDURAL'` → 490,
  of which 59 carry `payload` and 40 carry `metadata.triggers`. So
  ~90% of "procedural" memories are textual narratives with a `code_ref`,
  NOT engrams in any mechanistic sense — they're hooks into Python
  functions. The node-executor engrams are a minority. `pe_chain.py`
  never calls `reconsolidation.mark_recalled` / `confirm_recall` /
  `contradict_recall` despite REPLAN being exactly the place where a
  hypothesis should enter lability-on-contradiction.
- Blast radius: the claim that Igor's procedural knowledge IS engram-
  shaped is mostly theatre. If this is aired honestly, downstream docs
  (glossary, palace, brainstem core_patterns) all need truth-tracking
  edits. The `payload.cells` minority IS real engram — see Gap 1 which
  shows those are actually broken on disk.
- Biomimicry: **theatrical** (honest version: admit that Igor has two
  distinct procedural substrates — "habit-code-pointers" and "engrams
  with cells" — and they should have different `memory_type` tags, or at
  least different `metadata.habit_type` tags. Conflating them as
  "PROCEDURAL" makes the code lie to itself. Reconsolidation on pe_chain
  REPLAN is a natural match — the hypothesis WAS contradicted by the
  test failure, that's a textbook mismatch cue, and it should mark the
  prior PLAN memory labile).
- Proposed ticket:
  - id: T-engram-vs-habit-pointer-taxonomy
  - title: Split PROCEDURAL into engram vs. habit-pointer via metadata tag
  - size: M
  - tags: [memory, engrams, biomimicry, palace, docs]
  - description: 90% of PROCEDURAL memories are code-pointers (narrative
    + `metadata.code_ref`), not engrams (payload + triggers + executable
    cells). The architecture currently treats them interchangeably via
    `memory_type == 'PROCEDURAL'`, which hides the fact that only a
    minority are walked by `node_executor`. Fix shape: add a
    `metadata.execution_kind` tag with values `{code_pointer,
    engram_cell, compiled_chunk}` during a migration pass; update
    `basal_ganglia._score_habit` and the cursor runtime to use this tag
    rather than inferring from payload presence; update palace docs
    `theigors/igor/cognition` to describe both substrates. Does NOT
    change the `memory_type` enum (that would break every consumer) —
    this is purely additive metadata. Pair this with
    T-reconsolidation-on-pe-replan below. NOT high-inertia (migration +
    tag, no schema change). Emit a one-liner in T-docs-live-in-code for
    models.py docstring saying "PROCEDURAL is a family; see
    execution_kind tag for substrate."
  - disposal: **SHIP**

- Proposed companion ticket:
  - id: T-reconsolidation-on-pe-replan
  - title: Mark PLAN labile on REPLAN via reconsolidation.mark_recalled
  - size: S
  - tags: [memory, reconsolidation, pe_chain, biomimicry]
  - description: When `pe_close_loop` takes the fail branch into
    `_pe_replan` (pe_chain.py:1726), the prior PLAN memory (stored by
    `ops.store_plan`) is effectively being contradicted by the test
    outcome. This is the exact cue that should open a reconsolidation
    window on that PLAN memory so the revised plan can incorporate the
    failure signal rather than overwriting blind. Fix shape: after
    `basket.get('test_result').startswith('fail')` and before the
    tier.2 REPLAN call, call
    `reconsolidation.mark_recalled(plan_memory_id, reason='pe_replan_fail')`,
    pass through the replan, then on a passing subsequent test call
    `confirm_recall(plan_memory_id, merge=revised_plan_summary)`; on
    final escalation call `contradict_recall`. Scope: pe_chain.py only.
    Does NOT change the REPLAN prompt or basket shape. Tests: extend
    `tests/test_reconsolidation.py` with a pe_chain replan path
    assertion. Not high-inertia.
  - disposal: **SHIP**

### Finding P1.7 — Chunking is sequence→macro, not Miller chunking (persona 7)

- Verdict: **CONFIRMED_WORSE**
- Evidence: `wild_igor/igor/tools/habit_chunker.py:146-197` produces
  `CHUNK_<hash>` PROCEDURAL memories with `action_sequence` metadata.
  Live DB: 8 such CHUNK_ memories exist. Cross-check across the whole
  tree for `action_sequence` references: ONLY `habit_chunker.py` reads
  it. No consumer walks `action_sequence` at habit-selection time.
  `basal_ganglia.select_habit` does not prefer chunked predecessors.
  `cursor_runtime` does not treat a CHUNK as a macro-step. The chunks
  are observational debris.
- Blast radius: zero-currently-consuming. But shipping any honest use
  (e.g. "when PROC_A fires and a CHUNK_<A,B,C> exists, preemptively
  mark B,C as predicted for refractory skip on duplicate firing") would
  touch basal_ganglia's winner path, which is load-bearing. Honest
  chunking = Miller working-memory compression: one TWM slot holding the
  chunk handle instead of N slots holding its members. Current
  implementation neither frees TWM capacity nor shortcuts execution.
- Biomimicry: **theatrical**. The docstring header
  (habit_chunker.py:2-8) literally says "basal ganglia compresses
  repeated sequences into single chunks" — it doesn't; it writes a DB
  row nobody reads.
- Proposed ticket:
  - id: T-chunking-consumer-or-rename
  - title: Wire CHUNK_* as macro-predictor or rename to sequence_log
  - size: M
  - tags: [habits, chunking, biomimicry, twm]
  - description: `habit_chunker.py` discovers repeating PROC_ sequences
    and stores them as `CHUNK_` PROCEDURAL memories, but no code reads
    these. The naming claims Miller chunking; the behaviour is sequence
    logging. Two-path choice, pick one:
    (A) HONEST: rename module to `habit_sequence_logger.py`, rename
        memories to `SEQLOG_<hash>`, remove PROCEDURAL type claim.
        Small, low-risk. Preserves observability.
    (B) WIRE: add a consumer in `basal_ganglia.select_habit` that,
        when a winner is chosen, checks for a CHUNK_ whose first
        element is that winner; if found, schedule the downstream
        members into the refractory map as "predicted, suppress for
        5 min" so their firing must beat the chunk's confidence to
        win. This gives real working-memory-compression behaviour.
        Bigger change; touches basal_ganglia (MEDIUM inertia).
    Recommend starting with (A) now and filing (B) as a follow-up
    exploration. Either way, the code is currently misleading.
  - disposal: **SHIP (option A); DEFER option B to T-chunking-predictor-wire**

### Finding P1.8 — habit misfire taxonomy missing; pe_chain runaway escalation (persona 8)

- Verdict: **CONFIRMED**
- Evidence:
  - `misfire_counter.py` tracks only two misfire origins: bash exit 127
    (`record_bash_exit`) and an opaque `error_type` string via
    `record_tool_error`. No structured taxonomy — just a
    `(name, dispatch_path, error_type)` tuple. All habit-level misfires
    (e.g. "trigger collision", "context mismatch", "stale code_ref",
    "response incoherent") fold into the same file `misfire_log.jsonl`.
  - `habit_health_audit.py` maintains a hardcoded `_SYSTEM_HABITS` set
    (5 names) to detect system-habits-on-conversational-intent misfires
    — a single taxonomy slot.
  - `response_coherence_inhibitor.py` exists for off-topic response
    misfires (a separate taxonomy slot) but emits to TWM, not to
    misfire_counter.
  - pe_chain escalation: `_MAX_ATTEMPTS = 3` hard cap exists
    (pe_chain.py:1533). Good. BUT: the deduped channel-post in
    `_pe_escalate` (pe_chain.py:1936-1940) depends on
    `dedup_key=f"pe_chain:blocked:{ticket_id}:{reason[:80]}"` and a
    global in-process cache. Across restarts the dedup resets; with
    rapid flapping (the `T-scope-guard-reattempt-loop` mentioned in the
    code comment at line 1870), we get repeated channel spam. The
    code acknowledges this in the docstring and labels it a "short-term
    mitigation".
- Blast radius: observability — health audit is misleading (only one
  slot of misfire populated). Runaway ties up tier.2 budget. Dedup leaks
  on restart touch channel SNR for Akien.
- Biomimicry: **procedural-with-bio-name**. Habit misfires in biology
  are legibly distinct — Freudian slip ≠ perseveration ≠ stimulus
  confusion. Igor's misfire counter flattens all of them. Honest version
  has enum-typed misfire kinds with separate per-kind counters that feed
  their own inhibition layers.
- Proposed ticket:
  - id: T-misfire-taxonomy-enum
  - title: Structured misfire kind enum + per-kind counters
  - size: M
  - tags: [habits, observability, misfire, biomimicry]
  - description: Add a `MisfireKind` Enum: `{bash_127,
    tool_exception, context_mismatch, trigger_collision, stale_code_ref,
    response_incoherent, scope_blocked, replan_exhausted,
    trigger_matched_no_conditions}`. Refactor `misfire_counter.py` to
    accept a kind and record it in the JSONL plus aggregate via kind.
    Wire the three existing emitters: runner.py (bash_127 ✓ already),
    registry.py (tool_exception), response_coherence_inhibitor.py
    (response_incoherent), habit_health_audit.py `_detect_habit_misfires`
    (context_mismatch), pe_chain `_pe_escalate` (replan_exhausted or
    scope_blocked depending on reason). Expose top-misfire-kind via MCP
    `audit_conversation_health`. Does NOT change `tails` or TWM schemas.
    Does NOT touch basal_ganglia scoring. Sizing: ~100-150 LoC across
    4-5 files. Not high-inertia.
  - disposal: **SHIP**

- Proposed companion ticket:
  - id: T-pe-escalate-dedup-persisted
  - title: Persist pe_chain escalation dedup across restarts
  - size: S
  - tags: [pe_chain, observability, channel-noise]
  - description: `_post_to_channel(..., dedup_key=...)` uses
    in-process state. Igor restarts clear the cache, re-spamming the
    same ticket's block message. Fix shape: back the dedup with a small
    Postgres table `channel_dedup (key text pk, ts timestamptz,
    expires_at timestamptz)` or a shared TWM observation with a 30-min
    TTL. Pick whichever is already closest to channel_post. Scope: the
    `channel_post` module that backs `_post_to_channel`; pe_chain
    callers unchanged. Not high-inertia.
  - disposal: **SHIP**

### Finding P1.9 — response_coherence_inhibitor self-correction loop risk (persona 9)

- Verdict: **NEEDS_RUNTIME** (static reading suggests the loop is
  possible but not observed; need turn_trace check)
- Evidence: `response_coherence_inhibitor.py` (phase-1 detection, phase-2
  planned suppression per docstring). When incoherent, it writes a TWM
  marker. `main.py` narrative engine re-processes high-salience TWM
  markers. If the corrective narrative is ALSO incoherent, the inhibitor
  fires again on the new response. No static visit-count guard exists.
- Blast radius: a bounded oscillation. TWM TTL and refractory would
  eventually break it, but not before burning tier.2 budget.
- Biomimicry: **honest intent, incomplete**. A real prefrontal inhibitor
  has its own habituation / self-monitoring. The fix is an
  inhibitor-fires-counter with a hard escalate-to-human at N=3 per
  thread_id.
- Proposed ticket:
  - id: T-inhibitor-escalate-guard
  - title: Per-thread inhibitor-fires counter with N=3 escalate guard
  - size: S
  - tags: [inhibition, coherence, self-correction, safety]
  - description: Add a per-thread_id counter of response-coherence-
    inhibitor fires in a 10-minute window. On N=3, suppress further
    auto-correction and emit
    `COHERENCE_INHIBITOR_STUCK|thread=X|fires=N` to channel (deduped).
    Scope: response_coherence_inhibitor.py + a tiny in-process
    `collections.Counter` with TTL. Does NOT block the first 2 fires
    (those are useful). Testing: pytest by injecting 3 fake incoherent
    responses and asserting the escalation pathway. Not high-inertia.
  - disposal: **SHIP**

### Finding P1.10 — pe_chain replan loop coverage (persona 10)

- Verdict: **CONFIRMED_NARROWER**
- Evidence: `tests/test_coding_sprint.py` and related tests exercise
  chain paths but the REPLAN recursion at pe_chain.py:1723
  (`return pe_close_loop(basket)`) has no test that exercises the
  recursive `attempt_count`-bound ladder all the way to escalate. The
  pre-flight test at pe_chain.py:2010 is well-covered. The recursive
  tail call itself means a stack-depth cap IS `_MAX_ATTEMPTS` (3) —
  bounded. I cannot refute that tests exist somewhere — there are 2k+
  LoC in this file — but I didn't find one exercising the full
  pass→fail→replan-pass→commit sequence with real substitutions.
- Blast radius: low; this is a test gap, not a behaviour bug.
- Biomimicry: n/a — test coverage.
- Proposed ticket:
  - id: T-pe-replan-recursion-test
  - title: Integration test for pe_close_loop fail→replan→pass→commit
  - size: S
  - tags: [pe_chain, tests, coding-sprint]
  - description: Add a fixture-based integration test that stubs
    `_call_tier2` to return successive canned responses (first edit
    fails tests, second passes), then asserts that after two replans
    the basket reaches `commit_result` with expected content and
    `attempt_count==2`. Also add a test that exercises the
    `ESCALATION_NEEDED` channel post at attempt_count=2
    (pe_chain.py:1703). Scope: tests/ only. Not high-inertia.
  - disposal: **SHIP**

### Finding P1.12 — pe_chain should be engram, not Python (persona 12)

- Verdict: **CONFIRMED** (and the docstring at pe_chain.py:95-107 already
  acknowledges this as `PROC_CODE_A_TICKET_ENGRAM` future)
- Evidence: `pe_chain.py` is 2149 lines of linear Python with hard-coded
  control flow (pe_entry_init → pe_claim → ... → pe_close_loop). The
  docstring predicts reimplementation once engrams are stable. The
  ENGRAM_CODE_* seed (lab/claudecode/seed_coding_engrams.py) is a
  skeleton BRANCHIF chain — but see Gap 1 for why it's currently broken
  on disk.
- Blast radius: enormous. pe_chain is the spine of Igor's self-programming
  loop. Ripping it out now would brick the sprint pipeline. The honest
  path is incremental: (a) fix the ENGRAM_CODE_* cells so they actually
  execute (Gap 1), (b) verify the cursor_runtime can reach `pe_close_loop`
  parity, (c) then deprecate the Python chain.
- Biomimicry: **procedural-with-bio-name** in the sense that the
  subsystem is labelled "programming engrams" (T-programming-engrams in
  the docstring) but 100% of real work happens in Python. Honest stance
  today: the engram shape is a seed that isn't germinated yet.
- Proposed ticket:
  - id: T-pe-chain-engram-migration-plan
  - title: Write migration plan: pe_chain.py → PROC_CODE_A_TICKET_ENGRAM
  - size: M
  - tags: [pe_chain, engrams, design, architecture]
  - description: This is a design ticket, not code. Write a 1-page
    migration plan in palace (`theigors/igor/cognition/pe-engram-
    migration`) describing: (1) what the ENGRAM_CODE_* chain must do
    to reach parity with the Python pe_chain (step mapping, basket
    transit, error propagation, escalation); (2) whether the MCPCALL
    opcode needs any new features (streaming results? deadlines?
    retries?); (3) a test harness shape for dual-running
    pe_chain.py side by side with the engram version for N tickets
    before cutover; (4) deprecation plan for the Python
    step functions — keep them as MCPCALL targets, remove only
    run_pe_entry_chain. Does NOT write any code. Pairs with Gap 1
    (the current engram chain is broken; you can't plan a migration
    to a broken target). High-inertia consequence but design only.
  - disposal: **DEFER** (blocked by T-engram-trigger-cell-name-mismatch
    below — fix the engram structural bug first, THEN plan the
    migration)

## Pass 1 gaps (findings Pass 1 missed in your area)

### Gap 1 — ENGRAM_CODE_* triggers point to nonexistent cell names (LIVE BROKEN)

- Severity: **critical**
- Biomimicry: n/a — this is a structural bug that makes the engram
  mechanism inoperable; no biology-vs-mechanism question.
- Evidence: live DB query:
  ```
  SELECT id, metadata->'triggers', payload::text
  FROM memories WHERE id LIKE 'ENGRAM_CODE_%' LIMIT 3;
  →
   ENGRAM_CODE_INIT  | {"__entry__": "coding sprint entry"}
                     | {"cells": [["MCPCALL", "pe_entry_init", ...], ["BRANCHIF", true, "ENGRAM_CODE_CLAIM"]]}
  ```
  `node_executor.execute_node` (node_executor.py:136-146):
  ```
  triggers = memory.metadata.get("triggers", {})
  cell_name = triggers.get(fired_trigger)   # "coding sprint entry"
  ...
  cell = payload.get(cell_name)             # payload.get("coding sprint entry") → None
  if not isinstance(cell, list):            # triggers WARN, returns empty result
      log.warning(...)
      return result
  ```
  The seed script (`lab/claudecode/seed_coding_engrams.py:118,121`)
  writes `triggers={"__entry__": "coding sprint entry"}` BUT
  `payload={"cells": payload_cells}`. The trigger value "coding sprint
  entry" does NOT match the payload key "cells". Every attempt to walk
  this chain silently logs a WARNING and no-ops.
  Additional confirmation: the only places in the whole tree that
  reference `"coding sprint entry"` are (a) the seeder and (b) the
  docstring. Zero consumers.
  Additional confirmation: two habits
  (`PROC_INVOKE_SPRINT`, `PROC_INVOKE_COMMIT`) have
  `code_ref = "pe_chain:run_engram_cursor"` (live DB) — there is NO
  function `run_engram_cursor` in `pe_chain.py`. Grep confirms it only
  appears in `seed_skill_sprint_engram.py` and
  `seed_skill_commit_engram.py`.
- Proposed ticket:
  - id: T-engram-trigger-cell-name-mismatch
  - title: Fix ENGRAM_CODE_* triggers to point at "cells" payload key
  - size: S
  - tags: [engrams, pe_chain, critical, dead-code]
  - description: Two independent structural bugs conspire to make the
    engram-based coding chain dead on arrival: (1) `seed_coding_engrams`
    writes `triggers={"__entry__": "coding sprint entry"}` but the
    payload key is `"cells"` — `node_executor` looks up `payload.get(
    "coding sprint entry")`, finds nothing, logs WARN and no-ops;
    (2) two habits reference `code_ref=pe_chain:run_engram_cursor`
    which doesn't exist. Fix shape: change the seed to either
    `triggers={"__entry__": "cells"}` OR keep the human-readable name
    and make the payload key match (`payload={"coding sprint entry":
    [...]}`). Pick "cells" since that's the convention in
    node_executor's own docstring. Then RE-SEED all ENGRAM_CODE_*
    rows. Then either (a) add `run_engram_cursor` as a thin wrapper
    in pe_chain.py that loads the entry engram and calls
    `cursor_runtime.run_cursor`, or (b) rewrite the two PROC_INVOKE_*
    habits' code_refs to existing functions. Until this ticket lands,
    the ENGRAM cursor path for coding is decorative. Tests: seed a
    test engram in-memory, call execute_node, assert
    instructions_run > 0. NOT high-inertia (seed script + two habit
    rows + optional thin wrapper).
  - disposal: **SHIP** (this is the highest-stakes finding in-area —
    everything downstream about "engram migration" is blocked by it)

### Gap 2 — `MANAGEMENT_PHRASES` triggers are pure substring matching (one-word phrases can collide)

- Severity: **medium**
- Biomimicry: procedural-with-bio-name — "direct dispatch"
  (basal_ganglia.py:671-698) claims to bypass competition for reliability
  under load, but the mechanism is a word-boundary regex over a fixed
  phrase table. It's correct at the phrase level but each
  MANAGEMENT_PHRASES entry is trusted 1.0; an ambiguous utterance like
  "the coding sprint was a disaster, let me describe" would fire
  `PROC_CODING_SPRINT` at confidence 0.97.
- Evidence: basal_ganglia.py:103-145 table; basal_ganglia.py:679-698
  regex `\b{phrase}\b` over `raw_lower`. 30+ phrases, all flat-weight.
- Proposed ticket:
  - id: T-management-phrase-intent-gate
  - title: Gate MANAGEMENT_PHRASES by parsed intent before direct dispatch
  - size: S
  - tags: [habits, basal-ganglia, intent, safety]
  - description: MANAGEMENT_PHRASES direct-dispatch bypasses the intent
    gate that normal habits respect (`_apply_intent_gate`). A discussing/
    narrating mention of "coding sprint" or "queue drain" inside a
    conversational turn fires the management habit at 0.97. Add a
    guard: when `parsed.intent in {"conversation", "general",
    "explanation_request", "meta_question"}`, require the phrase to
    start the input or be prefixed by `:` / newline, else skip
    direct dispatch and let normal scoring handle it. Scope:
    basal_ganglia.py pre-check block (line 671-698 only). Preserve
    current behaviour for imperative intents. Testing: add cases to
    tests/test_bg_score_debug.py. Not high-inertia.
  - disposal: **SHIP**

### Gap 3 — `_refractory_map` is in-process global (not cleared on winner crash, leaks across tests)

- Severity: **medium**
- Biomimicry: honest in intent, leaky in implementation. A real
  refractory period is a per-neuron membrane-level mechanism — shared
  state across the whole population is wrong.
- Evidence: basal_ganglia.py:175 `_refractory_map: dict[str, float] = {}`
  — module-level. 15 references across the file. No lock. Never cleared
  except on natural expiry at :528-529.
- Proposed ticket:
  - id: T-refractory-map-thread-safety
  - title: Refractory map lock + forensic reset hook
  - size: S
  - tags: [basal-ganglia, concurrency, habits]
  - description: `_refractory_map` is a mutable module-level dict read
    and written during `select_habit`. Under the worker-pool pattern
    used elsewhere in main.py, two concurrent turns can both read the
    map, one expires an entry, the other reinstates it based on stale
    data. Add a `threading.Lock()` around the three mutation sites
    (:175, :529, :697, :849). Also expose a `reset_refractory()`
    helper that tests can call in fixtures. Not high-inertia.
  - disposal: **SHIP**

### Gap 4 — `_inhibit_neighbors` writes graph edges during selection (mutation in read path)

- Severity: **medium**
- Biomimicry: procedural-with-bio-name. Lateral inhibition IS biological.
  But writing durable interpretive_edges to Postgres from inside the
  habit-selection hot path (a) adds DB latency to every turn, (b) makes
  the graph quietly evolve without a commit boundary, (c) can corrupt
  the graph if `select_habit` is called in a dry-run / what-if mode.
- Evidence: basal_ganglia.py:552-584 writes `add_interpretive_edge` + a
  ring log inside `select_habit`'s normal path.
- Proposed ticket:
  - id: T-bg-inhibition-buffered-write
  - title: Buffer bg_inhibition edge writes; flush on turn-commit
  - size: S
  - tags: [basal-ganglia, cortex, performance, inhibition]
  - description: Move `_inhibit_neighbors` edge writes off the hot path.
    Collect (winner_id, target_id, weight, layer) tuples in a
    per-turn buffer exposed on the `bg_scoring` trace; flush them in
    a single batch `add_interpretive_edges_bulk` call from the
    turn-commit point in main.py. Preserves current semantics (edges
    still land in the graph), eliminates the mid-selection DB round-
    trip, and makes dry-run callers safe. Does NOT change inhibition
    logic. Not high-inertia.
  - disposal: **DEFER** (not urgent — flag as performance debt)

### Gap 5 — `pe_filter`'s HIGH-inertia check uses substring, duplicates scope_guard

- Severity: **medium**
- Biomimicry: n/a.
- Evidence: pe_chain.py:623-625:
  `_FILTER_HIGH_INERTIA = frozenset(["brainstem/", "memory/models.py",
  "cognition/reasoners/base.py"])`. Meanwhile
  `wild_igor/igor/tools/scope_guard.py` owns the canonical inertia
  classification (cited by persona 8 in Pass 1). Two sources of
  truth, both string-substring.
- Proposed ticket:
  - id: T-pe-filter-use-scope-guard
  - title: pe_filter delegates HIGH-inertia check to scope_guard
  - size: S
  - tags: [pe_chain, scope-guard, duplication]
  - description: pe_filter has a hardcoded 3-entry HIGH-inertia list
    while scope_guard maintains the authoritative tier table. Fix:
    replace pe_filter's `_FILTER_HIGH_INERTIA` check with a call to
    `scope_guard.classify_path(f)` and fail when any plan_file is
    HIGH. Keeps one source of truth and prevents drift (e.g. if
    Akien adds a file to brainstem, scope_guard gets updated; pe_filter
    silently remains permissive). Scope: pe_chain.py lines 623-678.
    Testing: extend existing pe_filter tests to cover non-obvious
    HIGH paths listed in scope_guard. Not high-inertia.
  - disposal: **SHIP**

### Gap 6 — `pe_close_loop` recurses unbounded outside the `attempt_count` guard

- Severity: **medium-low**
- Biomimicry: n/a.
- Evidence: pe_chain.py:1722 `return pe_close_loop(basket)`. If
  `_pe_replan` sets `hypothesis_error` and `_pe_implement` sets
  `implement_skipped=True`, `pe_test` re-runs the old tests (likely
  still failing), and `pe_close_loop` is called again, which increments
  `attempt_count`. `_MAX_ATTEMPTS=3` will eventually hit. BUT: there's
  NO guard against a malicious/malformed basket mutating
  `attempt_count` back down to 0 mid-chain.
- Proposed ticket:
  - id: T-pe-close-loop-iterative
  - title: Convert pe_close_loop recursion to while-loop
  - size: S
  - tags: [pe_chain, safety, minor]
  - description: Replace the tail-recursive `return pe_close_loop(basket)`
    at pe_chain.py:1722 with a `while attempt_count < _MAX_ATTEMPTS`
    loop. Functionally identical given current semantics, but (a)
    removes Python stack-depth concern, (b) makes `attempt_count`
    the ONLY loop variable (tamper-evident), (c) simplifies tracing.
    Scope: one function body. Not high-inertia.
  - disposal: **DEFER** (low impact; ship if another pe_chain ticket
    touches this function)

### Gap 7 — `pe_chain` calls Cortex(None) (uninitialized) to read GOAL

- Severity: **medium**
- Biomimicry: n/a — init smell.
- Evidence: pe_chain.py:254 and pe_chain.py:1144 both construct
  `_Cortex(None)` in helper functions, relying on the global singleton
  side effect. The cortex init path is subtle (Postgres URL fallback
  from `_paths()`). If the global isn't set before these helpers run
  (e.g. in tests), behaviour diverges from main runtime.
- Proposed ticket:
  - id: T-pe-chain-cortex-injection
  - title: Inject cortex into pe_chain helpers rather than Cortex(None)
  - size: S
  - tags: [pe_chain, di, tests]
  - description: Replace `Cortex(None)` construction inside
    `_get_active_goal` and `_get_coding_standards` with a module-level
    `_cortex = None` + `set_cortex(cx)` injection mirroring the
    basal_ganglia pattern (basal_ganglia.py:69-72). main.py wires it at
    boot. Tests can inject a mock. Scope: pe_chain.py helpers only.
    Not high-inertia.
  - disposal: **DEFER** (code-smell, not user-facing)

### Gap 8 — `run_habit_chunking` builds Cortex directly with sqlite-shaped path

- Severity: **medium**
- Biomimicry: n/a.
- Evidence: habit_chunker.py:129
  `cortex = Cortex(db_path=str(_paths().instance / "wild-0001.db"))`.
  This passes a `.db` file path to a Cortex that's supposed to go through
  db_proxy/Postgres. Violates CLAUDE.md rule "NO SQLITE ANYWHERE".
  Most likely currently harmless because Cortex.__init__ ignores the
  path when `IGOR_HOME_DB_URL` is set, but the code LIES about its
  substrate.
- Proposed ticket:
  - id: T-habit-chunker-remove-sqlite-path
  - title: habit_chunker stop passing SQLite path to Cortex constructor
  - size: S
  - tags: [habits, db, cleanup, rules-compliance]
  - description: `habit_chunker._upsert_chunk` constructs Cortex with
    `db_path=str(_paths().instance / "wild-0001.db")`. Everywhere
    else, Cortex is constructed with `None` and routes through
    db_proxy/Postgres. This SQLite-shaped init is either inert (good,
    delete it) or silently fallback-loading SQLite behaviour (very
    bad — see CLAUDE.md NO-SQLITE rule). Fix: replace with `Cortex(None)`
    to match the pattern used in pe_chain (pending T-pe-chain-cortex-
    injection). Scope: one line. Not high-inertia.
  - disposal: **SHIP**

## Dead-code cross-check

Live-DB query against `memories WHERE memory_type='PROCEDURAL' AND
metadata ? 'code_ref'` (116 distinct code_ref values across 490
procedural memories). Cross-referenced each code_ref against the
filesystem via Grep. Results scoped to this audit area:

- **Habits referencing non-existent code in your area:**
  - `PROC_INVOKE_SPRINT.code_ref = "pe_chain:run_engram_cursor"` —
    function does NOT exist in `wild_igor/igor/tools/pe_chain.py`.
    Only seed scripts reference the name. (see Gap 1)
  - `PROC_INVOKE_COMMIT.code_ref = "pe_chain:run_engram_cursor"` —
    same.
  - ENGRAM_CODE_* payloads MCPCALL `pe_entry_init`, `pe_claim`,
    `pe_read_ticket`, `pe_plan`, `pe_filter`, `pe_situate`,
    `pe_observe`, `pe_hypothesize`, `pe_implement`, `pe_test`,
    `pe_probe`, `pe_close_loop`. These functions DO exist (pe_chain.py
    has all of them) but they're NOT registered as tools via
    `registry.register`, so `MCPCALL` will hit the unknown-tool branch
    (node_executor.py:387-396). Registry lookup:
    `grep "registry.register" pe_chain.py` → shows only
    `run_pe_chain`, `run_pe_plan`, `run_pe_filter`, `run_pe_probe`
    registered (pe_chain.py:2076-2145). The per-step pe_* functions
    are NOT registered. So even if Gap 1 is fixed, `MCPCALL
    pe_entry_init` errors with "unknown tool".
    **This is a second structural bug layered on top of Gap 1.**

- **Code in your area not referenced by any habit or test (orphan
  candidates):**
  - `pe_run_bash` (pe_chain.py:1008) — basket-aware bash wrapper,
    intended for "tpl-layer4-run-bash code_ref slot" per docstring.
    Grep: no habit `code_ref` references it, no test references it.
    Possibly orphaned; investigate whether a layer4 habit still
    needs it.
  - `_situate_from_memory` (pe_chain.py:681) — only called from
    `pe_situate`. OK, not orphan.
  - `MisfireCounter.reset_counter` (misfire_counter.py:209) — only
    called in tests. OK.
  - `MisfireCounter.get_threshold_exceeded` (misfire_counter.py:183)
    — grep'd, no production caller; only tests and the docstring.
    Potential orphan or a planned "surface repair candidates"
    consumer that was never wired.
  - The 8 CHUNK_* memories in the DB (see Finding P1.7) have zero
    consumers — they are data-orphan rows rather than code orphans.

Additional flag: two habits in live DB have NULL code_ref:
`PROC_CODE_A_TICKET` and `PROC_HABIT_COMPILER` (from the SELECT above).
These are "narrative-only" habits where the narrative is the actionable
instruction for the LLM. Honest shape if this was the intent —
otherwise both are broken. PROC_HABIT_COMPILER is especially suspect
since basal_ganglia has a COMPILE_PHRASES pre-check that returns it
at confidence 0.95; what fires when it wins is unclear without a
code_ref. Open as investigate-only:

- id: T-null-coderef-habits-investigate
- title: Investigate habits with NULL code_ref (PROC_CODE_A_TICKET,
  PROC_HABIT_COMPILER)
- size: S
- tags: [habits, investigate, audit]
- description: Two live habits have `metadata.code_ref` absent.
  Determine whether this is intentional (narrative-as-instruction to
  LLM) or rot (the code_ref was removed but habit kept firing).
  If intentional, add a `metadata.habit_mode = "narrative_only"` tag
  and document in palace. If rot, either restore a code_ref or retire
  the habit. No code changes until we know.
- disposal: **INVESTIGATE**

## Summary

- Ticket candidates total: **15**
  - T-bg-bare-except-hardening (SHIP)
  - T-rename-hebbian-to-coactivation-counter (SHIP)
  - T-engram-vs-habit-pointer-taxonomy (SHIP)
  - T-reconsolidation-on-pe-replan (SHIP)
  - T-chunking-consumer-or-rename (SHIP option A; DEFER option B)
  - T-misfire-taxonomy-enum (SHIP)
  - T-pe-escalate-dedup-persisted (SHIP)
  - T-inhibitor-escalate-guard (SHIP)
  - T-pe-replan-recursion-test (SHIP)
  - T-pe-chain-engram-migration-plan (DEFER)
  - T-engram-trigger-cell-name-mismatch (SHIP — critical)
  - T-management-phrase-intent-gate (SHIP)
  - T-refractory-map-thread-safety (SHIP)
  - T-bg-inhibition-buffered-write (DEFER)
  - T-pe-filter-use-scope-guard (SHIP)
  - T-pe-close-loop-iterative (DEFER)
  - T-pe-chain-cortex-injection (DEFER)
  - T-habit-chunker-remove-sqlite-path (SHIP)
  - T-null-coderef-habits-investigate (INVESTIGATE)

  (Count: 19 tickets when including the sub-option for chunking as a
  separate ticket and the SHIP/DEFER split on a couple.)

- Recommended **SHIP: 12**
  (T-bg-bare-except-hardening, T-rename-hebbian-to-coactivation-counter,
  T-engram-vs-habit-pointer-taxonomy, T-reconsolidation-on-pe-replan,
  T-chunking-consumer-or-rename [A], T-misfire-taxonomy-enum,
  T-pe-escalate-dedup-persisted, T-inhibitor-escalate-guard,
  T-pe-replan-recursion-test, T-engram-trigger-cell-name-mismatch,
  T-management-phrase-intent-gate, T-refractory-map-thread-safety,
  T-pe-filter-use-scope-guard, T-habit-chunker-remove-sqlite-path —
  14 by strict count)

- Recommended **DEFER: 5**
  (T-pe-chain-engram-migration-plan — blocked by Gap 1;
  T-bg-inhibition-buffered-write — perf debt not urgent;
  T-pe-close-loop-iterative — fold into next pe_chain touch;
  T-pe-chain-cortex-injection — code-smell;
  T-chunking-predictor-wire option B — after rename lands)

- Recommended **INVESTIGATE: 1**
  (T-null-coderef-habits-investigate)

- Recommended **DISCARD: 0** — every finding in this area corresponds
  to real code. The bar for DISCARD would be "Pass 1 described
  something that no longer exists"; none of the area 2 findings
  refute cleanly.

- Highest-stakes single finding in this area:
  **T-engram-trigger-cell-name-mismatch (Gap 1).** The ENGRAM_CODE_*
  chain is structurally dead — triggers point at a cell name that
  doesn't exist in the payload, and the MCPCALL targets aren't in the
  tool registry. Every piece of "Igor is moving toward engram-native
  self-programming" is load-bearing on a subsystem that currently
  logs WARN and no-ops. Fix this first; every other engram-forward
  ticket (including P1.12 "chains→networks") is blocked by it.

- Top biomimicry-honesty call:
  **T-engram-vs-habit-pointer-taxonomy.** 450 out of 490 "PROCEDURAL"
  memories are code-pointers, not engrams. The codebase treats them
  identically. Pass 1 caught the single-node problem; what Pass 1
  missed is the TWO-substrate problem — Igor has a real minority of
  engrams (with cells) and a huge majority of Python-function-pointer
  habits sharing the same memory_type. Naming this honestly via
  `metadata.execution_kind` lets downstream code stop lying to itself
  about what "procedural" means.

- One sentence for Pass 3:
  **Pass 3 should verify whether T-engram-trigger-cell-name-mismatch
  fix is in-scope for the current CP cornerpost window or whether it
  should land as a prerequisite to the persona-12 "chains→networks"
  epic — and whether PROC_INVOKE_SPRINT / PROC_INVOKE_COMMIT should be
  retired outright since their stated intent (engram-driven skill
  invocation) is two hops from operational.**
