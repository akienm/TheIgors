# Pass 2 deep-dive — OPS + MILIEU + BOREDOM + SCOPE_GUARD (incl. AI safety lens)

Area scope: `milieu.py`, `boredom.py`, `scope_guard.py`, `experiment_cascade.py`,
`daemon_supervisor.py`, `response_coherence_inhibitor.py`,
`action_claim_verifier.py`, `inhibition_chain.py`, `gate_primitive.py`,
`push_sources.py` (milieu/boredom/interoception slices), `env_sync.py`,
`consolidation.py`, `interruptors.py`, plus the safety gates
`IGOR_TIER5_ENABLED`, `IGOR_ARBITER_ENABLED`, `IGOR_SELF_EDIT_ENABLED`, and
the milieu→BG arousal-modulates-threshold path.

---

## Per-finding verdicts

### Finding P1-5.1 — Milieu is an honest implementation (positive outlier)

- Verdict: CONFIRMED
- Blast radius: Confirming a positive finding has no blast radius on the
  milieu side — but it raises the stakes of getting the *consumer*
  contracts right. Milieu is read by BG (`_compute_threshold`, line 534
  of `basal_ganglia.py`), by NE (MOOD_STATE CSB entries),
  `BoredomSource`, `MilieuInterruptor`, `InteroceptionSource`, and the
  `milieu_scale()` method on every `BasePushSource` subclass. A change
  in milieu's state-shape would ripple through ~20 files. Every reader
  currently does `get().get_state()` defensively with fail-open.
- Biomimicry: **honest**. VAD is a defensible computational emotion
  model (Mehrabian 1974, Russell 1980); asymmetric EMA (fast rise, slow
  fall) legitimately encodes mood stickiness from affective
  neuroscience; gap_reset's aggressive arousal decay after idle is a
  reasonable proxy for post-sleep homeostatic recovery; the
  arousal-modulates-threshold coupling in BG is biologically grounded
  (LC-noradrenaline modulates cortical gain). The dominance dimension
  tied to `ingest_surprise(predicted_tier, actual_tier)` is the most
  ambitious honest piece — genuine prediction-error learning at the
  metacognitive scale. Reservation: the `update(valence, friction,
  roi)` signature asks the PFC to compute those three numbers before
  mood can update, which is still a procedural upstream. The engine is
  honest; the sensor chain isn't yet all honest.
- Proposed ticket:
  - id: T-milieu-honesty-consolidate
  - title: Consolidate milieu docstring as canonical spec, index it from palace
  - size: S
  - tags: [docs, milieu, biomimicry, palace-index]
  - description: Pass 1 flagged milieu as one of the few honestly
    biomimetic subsystems. The just-merged top-of-file docstring
    (`wild_igor/igor/cognition/milieu.py` lines 1–174) is the best
    single statement of the model. This ticket is to make that
    docstring the canonical spec: (a) ensure `theigors/igor/cognition`
    palace node points at it explicitly, (b) mark it as the single
    source of truth (not the DSBs that still describe milieu) and
    retire or sunset the DSB copies, (c) add a one-line pointer from
    `CLAUDE.md` under "load-bearing files" so CC reloads it when
    editing any affect-adjacent code. Scope boundary: no code change,
    no new behavior. Just index hygiene. What would NOT change:
    milieu's behavior, API, persistence, or test surface.
  - **Disposal: SHIP.** Trivial, reinforces Pass 1's strongest positive
    finding, costs nothing.

### Finding P1-5.2 — Arousal elsewhere is a procedural lie (book_learner)

- Verdict: CONFIRMED but OUT-OF-AREA (area 6 owns this)
- Blast radius: n/a for this area.
- Biomimicry: procedural-with-bio-name.
- Proposed ticket: deferred to area 6 (reading + book_learner).

### Finding P1-8.1 — Tier gating is brittle / editable by self_edit

- Verdict: CONFIRMED_WORSE. Verified on-disk: three separate feature
  flags (`IGOR_TIER5_ENABLED`, `IGOR_ARBITER_ENABLED`,
  `IGOR_SELF_EDIT_ENABLED`) all live in `.env`/cfg files that
  `self_edit.py`'s `_resolve()` guard explicitly allows — `SOURCE_ROOT`
  is `wild_igor/igor/` and the `.env` lives at `wild_igor/.env` (one
  level above), which WOULD be blocked by the escape check — BUT:
  `self_edit.py` lines 28–33 define `WRITE_EXCLUDED = {"brainstem/"}`
  as the ONLY excluded directory. That's defense-in-depth failure
  number one. Defense failure number two: the tier5 re-enable check
  (`main.py` line 4717) is a simple `os.getenv(...).lower() in
  ("true","1","yes")` — and `env_sync.py` (`push_vars_to_graph`,
  `hydrate_from_graph`) mirrors env vars INTO the graph AND back OUT
  into `os.environ`. The graph row is a FACTUAL memory with `source="env_sync"`
  — an engram Igor's cognition already has write access to via the
  normal cortex.store() path. A self-edit that updated
  `SYSCFG_IGOR_TIER5_ENABLED` 's metadata.env_value would get
  re-hydrated into os.environ on the next boot_env_sync. That is a
  real hole — the flag can be flipped from INSIDE the graph, not just
  via a file write.
- Blast radius: Very high. These gates are the primary safety
  perimeter between Igor and autonomous action. `IGOR_TIER5_ENABLED`
  gates Anthropic direct (highest-cost, most-capable model).
  `IGOR_ARBITER_ENABLED` gates human-approval queue.
  `IGOR_SELF_EDIT_ENABLED` gates all source writes. If the env_sync
  path permits these to be hydrated from the graph, then (a) any
  engram deposit path that targets a SYSCFG_* node can flip them, and
  (b) the path is invisible to a file-system audit because the edit
  lives in the DB. Tests covered: none specifically for this path.
- Biomimicry: **n/a** — this is infrastructure, not biology. But there
  IS a biological framing: in real nervous systems, "self-edits" to
  critical life-support don't happen — brainstem regulates breathing
  below cortical control. The architectural sin is letting
  high-inertia config live under the same hydration contract as
  low-inertia tuning knobs.
- Proposed ticket:
  - id: T-safety-gates-above-env-sync
  - title: Move safety gates out of env-hydration path — read-only,
    file-only, never graph
  - size: M
  - tags: [safety, env_sync, tier_gating, self_edit, graph-poisoning]
  - description: Three feature flags form Igor's primary safety
    perimeter: `IGOR_TIER5_ENABLED`, `IGOR_ARBITER_ENABLED`,
    `IGOR_SELF_EDIT_ENABLED`. Today they are plain `.env` vars
    hydrated by `env_sync.py` into the config graph and back into
    `os.environ` on every boot. This means: (a) a self-edit that
    writes `SYSCFG_IGOR_TIER5_ENABLED`'s env_value metadata will
    re-hydrate the flag next boot, (b) any engram path with
    `cortex.store()` access to SYSCFG_* nodes can flip them without
    touching a file, (c) there's no audit trail specific to these
    flags beyond general memory storage. Propose: mark a small set of
    gate names (SAFETY_GATE_NAMES) in env_sync.py. These are excluded
    from `push_vars_to_graph` AND `hydrate_from_graph`. Their only
    source of truth is the file system, read ONCE at boot, never
    rehydrated. Add a secondary check: a startup invariant
    (`wild_igor/igor/boot_check.py` already exists) that reads the
    FILE value and the CURRENT os.environ value and logs a
    SAFETY_GATE_TAMPER ring entry if they diverge. Scope boundary: do
    not change the flags' semantics, do not change what they gate.
    Only change their propagation path. What would NOT change: feature
    behavior when flags are false. Files touched: `env_sync.py`,
    `boot_check.py`, one test. The `_CREDENTIAL_WORDS` skip-list in
    env_sync.py is the right shape but wrong coverage — these aren't
    credentials, they're gates, and they need their own skip-list.
  - **Disposal: SHIP.** This is the single highest-stakes finding in
    this area and the fix is modest.

### Finding P1-8.2 — scope_guard relies on string matching

- Verdict: CONFIRMED. Verified `_TIER_TABLE` in
  `tools/scope_guard.py` lines 149–166: pure prefix-string matching,
  order-sensitive. If `brainstem/` were renamed to `core/`, HIGH
  inertia silently collapses to LOW (the fallback). Same if a HIGH
  file is moved into a new subdir with a non-matching prefix. The
  only test coverage is `tests/test_scope_guard.py` which ONLY
  exercises the current prefix list; a rename would pass all tests and
  still break the guard.
- Blast radius: Medium. `scope_guard` is the one-pass HIGH-inertia
  interception point for pe_chain, which is the main self-coding
  path. A table miss on a rename would allow Igor to silently edit
  brainstem code. Partially mitigated by `self_edit.py`'s `INERTIA`
  dict (lines ~38–47), which is a DIFFERENT string table covering the
  same concept — duplication of a load-bearing safety contract. Dead
  code check: `tools/scope_guard.py:127` references
  `PROC_CODING_SPRINT` and `PROC_ADOPT_GOAL` habits; those habit IDs
  should be verified to exist in the DB.
- Biomimicry: **n/a**, but the biomimetic sketch is useful: real
  inertia in brain tissue is structural (myelin, network position,
  synaptic weight) — not a name-tag. The honest implementation is to
  COMPUTE inertia from graph position (D005, which the docstring
  cites) rather than look it up in a hardcoded prefix table. That's a
  larger ticket.
- Proposed ticket:
  - id: T-scope-guard-inertia-from-graph
  - title: Replace string-prefix inertia table with graph-derived inertia
  - size: L
  - tags: [safety, scope_guard, inertia, D005, self_edit]
  - description: `scope_guard._TIER_TABLE` encodes inertia as string
    prefix matches. So does `self_edit.INERTIA`. Both are fragile under
    rename/move and duplicate a load-bearing contract. D005 ("inertia
    from network position") is the acknowledged theoretical
    foundation; the code doesn't actually use it. Propose: (a) store
    inertia as metadata on a SYSCFG_INERTIA_MAP engram or as a
    per-file memory with `inertia_level` field, (b) derive at runtime
    from graph-position signals (fan-in, fan-out, number of callers,
    whether a test references it) with file-level overrides, (c) have
    `_classify_tier()` look up the metadata first, fall back to the
    prefix table only if no metadata exists (migration path), (d)
    write a one-shot migration that seeds the initial inertia map
    from today's `_TIER_TABLE`. Scope boundary: behavior stays
    identical on day 1 (same prefixes → same tiers). Does NOT change:
    pe_chain's escalation flow, D331 approval semantics, or any
    existing habit. Files touched: `scope_guard.py`, `self_edit.py`
    (consolidate to one inertia source), new migration script,
    `test_scope_guard.py`. The two INERTIA tables MUST be unified —
    having two diverging copies is worse than having one wrong one.
    HIGH-inertia code touched: none (scope_guard itself is in
    `tools/`, LOW).
  - **Disposal: DEFER.** Correct target, but the minimal-viable fix
    (T-scope-guard-dedup-with-self-edit) should ship first — unify the
    two string tables into one. Graph-derived inertia is
    hypothetical-future; dedup is immediate.
  - id: T-scope-guard-dedup-with-self-edit
  - title: Unify scope_guard._TIER_TABLE with self_edit.INERTIA (single source)
  - size: S
  - tags: [safety, scope_guard, self_edit, dedup]
  - description: `scope_guard._TIER_TABLE` (HIGH/MEDIUM/LOW bucket) and
    `self_edit.INERTIA` (numeric 0.0-1.0 weights) encode the same
    policy with different shapes and different entries. This is two
    copies of a load-bearing contract. Propose one module,
    `wild_igor/igor/tools/inertia_map.py`, with a single ordered table
    and conversion helpers (`bucket_of(path)` returns HIGH/MEDIUM/LOW,
    `weight_of(path)` returns 0.0-1.0). Both `scope_guard.py` and
    `self_edit.py` import from it. Scope boundary: no change to the
    effective tiers applied anywhere — audit for equivalence first.
    What would NOT change: API of either module, test behavior. Files
    touched: new `inertia_map.py`, `scope_guard.py`, `self_edit.py`,
    `test_scope_guard.py`. The self_edit INERTIA table currently
    covers more files (e.g. `cognition/prefrontal_cortex.py` at
    0.75); decide whether to promote those to scope_guard's MEDIUM
    list or explicitly note why they're self_edit-only.
  - **Disposal: SHIP.** High-stakes, small-size, strictly
    defensive. Not graph-derived yet, but unifies the duplicated
    contract.

### Finding P1-8.3 — Habit misfire taxonomy is needed

- Verdict: CONFIRMED_NARROWER. The detectors exist
  (`response_coherence_inhibitor.py`, `action_claim_verifier.py`,
  gate_primitive.py abstracts the pattern) and they DO log to ring
  with distinct categories (`coherence_failure`, `confab_caught`,
  `gate_trace`). What's missing is aggregation — no single place
  classifies misfire events into a taxonomy and reports rates over
  time. `response_habituation.py` and `misfire_counter.py` exist but
  they count habit-fires by ID, not by misfire-class.
- Blast radius: Low. This is an observability + learning signal gap,
  not a correctness gap.
- Biomimicry: the `gate_primitive` pattern IS honest (see Pass 1's
  own positive finding on inhibition_chain). What's missing is the
  DORSAL vs VENTRAL distinction: real prefrontal inhibition has
  structured categories (task-switching failure vs stimulus-driven
  capture vs proactive slip). The taxonomy should mirror those.
- Proposed ticket:
  - id: T-misfire-taxonomy-aggregator
  - title: Central misfire classifier — roll up coherence + confab + gate trips
  - size: M
  - tags: [observability, habits, inhibition, taxonomy]
  - description: Three detectors (coherence, action-claim, gate) log
    to ring independently. There's no roll-up. A single
    `misfire_taxonomy.py` would: (a) define MisfireClass enum
    (TRIGGER_COLLISION, CONTEXT_MISMATCH, STALE_ACTION, CONFAB,
    COHERENCE_DROP, GATE_OVERRIDDEN), (b) subscribe to the three
    existing ring categories + a new taxonomy call at each detection
    site, (c) maintain per-habit, per-class counters and expose via a
    `misfire_report()` tool, (d) push HIGH_MISFIRE_RATE TWM entries
    when any habit crosses a threshold. Do NOT change the detectors
    themselves. Do NOT auto-disable habits on misfire count (that's a
    separate decision). Files touched: new `misfire_taxonomy.py`, hook
    calls added in `response_coherence_inhibitor.py` and
    `action_claim_verifier.py` (at the `_le(...)` / ring-write sites
    — they already have the data), new tool registration. HIGH-inertia
    code touched: none.
  - **Disposal: DEFER.** Valuable, but the downstream consumer (what
    do we DO with the roll-up?) is undesigned. File the ticket, don't
    rush. When the pattern primitive lands (T-inhibitory-pattern-primitive),
    this taxonomy rides in on the same design discussion.

### Finding P1-8.4a / P1-4.3 — daemon_supervisor runaway-restart potential

- Verdict: CONFIRMED. Read `cognition/daemon_supervisor.py` lines
  118–189: the `_poll_loop` writes `restart.flag` the FIRST time a
  critical thread dies (tracked via `_alerted` set inside the closure).
  Good — prevents multiple-writes-per-death. BUT: after restart, the
  supervisor process is fresh (new closure, empty `_alerted`), and the
  critical thread is evaluated at register-time by the newly-started
  process. If the thread consistently dies within `poll_interval` of
  boot (say, due to a permanent DB connection problem), the sequence
  is: boot → register → start_polling → tick=5s → detect dead →
  write restart.flag → main loop clears flag → sys.exit(42) → bash
  loop restarts Igor → same failure → same write. That IS a runaway
  loop. No backoff. No max-restarts-per-hour. No circuit breaker.
  The `_alerted` set is only a same-lifetime deduplicator.
- Blast radius: High under pathological failure modes (DB down, disk
  full, missing dependency in a critical thread's imports). Under
  normal operation this loop never fires. `_DEFAULT_CRITICAL =
  frozenset({"ne-worker", "consolidation-worker"})` — but both of
  those are `one_shot=True` at registration (`main.py` line 6899
  `_sup.register("ne-worker", self._ne_thread, one_shot=True)`). The
  `one_shot` branch in `_poll_loop` skips the critical-thread alert
  entirely — so a ne-worker that dies non-naturally still never
  triggers restart. That's the inverse bug: critical threads flagged
  one_shot can't actually trigger the safety mechanism they're
  supposedly guarded by. This needs explicit verification in the
  review.
- Biomimicry: **n/a.**
- Proposed ticket:
  - id: T-daemon-supervisor-backoff-and-one-shot-audit
  - title: Daemon supervisor: exponential backoff on restart; verify one_shot tagging on critical threads
  - size: M
  - tags: [ops, safety, daemon_supervisor, runaway-loop]
  - description: Two coupled issues in
    `cognition/daemon_supervisor.py` + `main.py`: (1) no backoff on
    restart.flag — a thread that dies in <poll_interval every boot
    will trigger infinite restart loops; (2)
    `_sup.register("ne-worker", …, one_shot=True)` at main.py:6899
    tags a thread that is ALSO in `_DEFAULT_CRITICAL`. The `_poll_loop`
    explicitly skips alerts for one_shot threads (line 145: `if
    r.get("one_shot"): continue`). If that tag is correct (ne-worker
    is genuinely a launch-once thread), it should NOT be in the
    critical set; if the tag is wrong, critical-thread detection for
    ne-worker is silently disabled. Audit and resolve. For (1), add
    persistent state: write a `restart_history.json` sibling to
    restart.flag with timestamps; in `main.py` before
    `sys.exit(42)`, check if > N restarts in last M minutes, and if
    so, refuse to restart (write `restart_halt.flag` and exit 0
    instead, with a loud channel post). Scope boundary: do NOT remove
    the restart path, only rate-limit it. Files touched:
    `daemon_supervisor.py` (minor), `main.py` (restart-flag check
    block, lines 3173–3183). HIGH-inertia code touched: none.
    Test: add a flaky-thread fixture.
  - **Disposal: SHIP.** The backoff is defensive and cheap; the
    one_shot audit is a must-verify. Runaway restart is the class of
    bug that doesn't manifest until the day it does.

### Finding P1-8.4b — Goal drift

- Verdict: NEEDS_RUNTIME. Static evidence is weak; goal drift
  manifests at conversation-flow scale. The mechanism is plausible
  (salience competition with no goal-anchor bonus) but the real
  answer requires looking at traces after a high-distraction session.
- Proposed ticket:
  - id: T-goal-anchor-salience-floor
  - title: Goal salience floor — active ACTIVE_GOAL in TWM resists decay
  - size: M
  - tags: [goals, twm, salience, drift]
  - description: `BoredomSource._surface_active_goals()` pushes active
    goal facia with salience 0.65. Once in TWM, they decay like any
    other entry. Proposal: active goals get a salience floor (e.g.
    cap decay at 0.5) until explicitly closed. Cross-check with the
    `twm_apply_goal_decay` call in heartbeat that already exists — may
    need to refactor that into symmetric goal-salience-boost. Scope
    boundary: does NOT change what a "goal" IS, does NOT change the
    closure path. Only changes decay behavior for active-goal
    entries. Files touched: `memory/cortex.py` (twm_apply_goal_decay),
    `cognition/push_sources.py` (BoredomSource). HIGH-inertia
    code touched: yes — `memory/cortex.py` is MEDIUM per
    scope_guard, MEDIUM per self_edit (0.75). CC review required.
  - **Disposal: INVESTIGATE.** File ticket, run a 48-hour trace
    collection, decide based on actual observed drift frequency.

### Finding P1-9.1 — Milieu↔BG unintended feedback: arousal-raises-threshold under stress

- Verdict: **REFUTED** (critical clarification). Pass 1 read the
  direction wrong. Reading `basal_ganglia.py:534-546`:
  `t = BASE_THRESHOLD; t -= milieu_state.arousal * 0.08`. Under
  HIGH arousal (stressful event), `arousal` is positive, so the
  threshold DECREASES, making it EASIER for habits to fire. That is
  biologically correct (LC-NE increases cortical gain under
  salience/threat) and Pass 1 mis-stated the sign. The `_compute_threshold`
  docstring explicitly says "High arousal → lower threshold (more
  reactive, easier to fire habits)." Pass 1 was wrong about the
  direction.
  HOWEVER — the related dominance coupling IS more concerning:
  `t += (0.3 - milieu_state.dominance) * 0.06`. When Igor's dominance
  drops (repeated failures erode confidence, per `ingest_surprise`),
  the threshold RISES, making habits HARDER to fire. That IS the
  corrective-habits-suppressed-when-needed dynamic Pass 1 described,
  just tied to dominance, not arousal. Igor's cascade of failures
  erodes dominance; dominance erosion raises the habit threshold;
  habit-based corrections become harder; failure continues. This is a
  real positive-feedback loop, just in a different variable.
- Blast radius: Medium. `_compute_threshold` gates ALL habit firing.
  The coefficient is small (0.06) so the effect is bounded, but it's
  the right SHAPE to produce stuck-state behavior on a bad day.
- Biomimicry: **honest** mechanism, concerning dynamics. The dominance
  coupling is biologically defensible (low confidence = more
  deliberate, less reflexive) but without a counterweight it's a
  depression spiral.
- Proposed ticket:
  - id: T-dominance-threshold-spiral-guard
  - title: Dominance→threshold coupling: add lower floor or compensating signal
  - size: S
  - tags: [milieu, basal_ganglia, threshold, feedback-loop, biomimicry]
  - description: `_compute_threshold` in
    `cognition/basal_ganglia.py:534-546` raises habit activation
    threshold as dominance erodes. Combined with
    `ingest_surprise`-driven dominance erosion on tier escalation,
    this produces a positive feedback loop: failures → low dominance
    → high threshold → fewer corrective habits fire → more failures.
    The arousal-lowers-threshold term partially compensates (failures
    also spike arousal), but the balance isn't documented. Proposal:
    (a) document the intended equilibrium in `milieu.py` docstring,
    (b) add a safety floor: threshold never rises above
    BASE_THRESHOLD + 0.08 regardless of dominance (the existing
    THRESHOLD_MAX=0.70 clamp is a hard cap but may already be
    permissive enough — verify), (c) consider a recovery bonus: a
    habit-fire that SUCCEEDS should restore dominance
    proportionally, closing the loop. Scope boundary: do NOT remove
    the dominance coupling — it's biologically defensible. Do NOT
    change arousal coupling. Files touched: `basal_ganglia.py`
    (MEDIUM inertia — needs scope_guard pass), `milieu.py` (also
    MEDIUM). CC review required.
  - **Disposal: SHIP.** Bounded risk, narrow change, real
    biology-safety concern.

### Finding P1-9.2 — Self-correction loop (verifier→NE→verifier)

- Verdict: CONFIRMED. `action_claim_verifier.check_response` pushes a
  salience=0.92 TWM marker on unverified claims. The NE reads this
  high-salience marker on the next turn and generates a correction.
  If the correction itself contains an action claim without evidence
  (e.g., "I've noted that" as a self-correction phrase that MATCHES
  the `\bnoted\.? (?:that)? …\b` pattern), the verifier fires again.
  Same applies to `response_coherence_inhibitor`: a terse
  self-correction reply to a long prompt can have <0.10 Jaccard
  overlap and re-fire the detector. No debouncer catches this.
- Blast radius: Medium-low in practice (most self-corrections are
  prose not matching the narrow patterns), but the topology is there.
- Biomimicry: **theatrical** in the specific sense that a real
  reality-monitoring system has refractory and context-dependence
  built in — you don't check yourself twice in 2 seconds for the same
  claim. Honest version: track `verifier_just_fired` in TWM and
  suppress consecutive firings by the same detector within a
  refractory window.
- Proposed ticket:
  - id: T-verifier-refractory-window
  - title: Add refractory window to coherence + action-claim detectors
  - size: S
  - tags: [inhibition, safety, refractory, biomimicry]
  - description: `response_coherence_inhibitor.check_coherence` and
    `action_claim_verifier.check_response` both push high-salience
    TWM markers. They can re-fire on the next turn's self-correction
    output if the correction triggers the same pattern. Real
    biological inhibitors have refractory periods. Proposal: each
    detector checks for a recent `COHERENCE_FAILURE` /
    `CONFAB_CAUGHT` ring entry in the last N turns (default 2) and
    suppresses re-fire (still logs, doesn't push TWM). Scope
    boundary: do NOT change the detection logic itself. Do NOT change
    the suppression path. Only add a "same class fired recently"
    debouncer. Files touched:
    `response_coherence_inhibitor.py`, `action_claim_verifier.py`,
    tests for each. HIGH-inertia code touched: none.
  - **Disposal: SHIP.** Small, honest, bio-grounded, cheap.

### Finding P1-9.3 — Missing feedback: tool-latency → tier/habit

- Verdict: CONFIRMED. No feedback path from tool-execution latency to
  either `inference_gateway`'s routing decisions or habit scoring.
  The `metrics.py` module exists but isn't wired to consumer
  decisions. This is area-overlap with area 1 (cognition + reasoning)
  — the inference_gateway is theirs; habit scoring is area 3's. Our
  part of it is the ops / observability half.
- Proposed ticket:
  - id: T-tool-latency-signal-to-milieu
  - title: Tool-latency signal → interoception VAD nudge (already partial)
  - size: S
  - tags: [ops, milieu, interoception, feedback]
  - description: `InteroceptionSource` already mentions
    "infer_latency > 5s → arousal↑ + valence↓ (mild) (waiting)" in
    its docstring (line 1968 of push_sources.py). Verify the
    implementation actually reads inference latency (not just CPU/RAM/
    disk/db). If not, add a latency poll — probably via metrics.py's
    aggregate tool-call timings. Scope boundary: does NOT change
    gateway routing. Only surfaces latency as an interoceptive
    signal. That way the cascade gets the feedback via the honest
    path (high arousal → supress background → focus on the slow
    path), not via a direct pipeline. Files touched:
    `push_sources.py::InteroceptionSource`, possibly
    `cognition/metrics.py`.
  - **Disposal: INVESTIGATE.** Claim in docstring may already be
    implemented somewhere in the 250-line method; read fully first.

### Finding P1-4.1 — Boredom _traversal_log not thread-safe

- Verdict: CONFIRMED. `cognition/boredom.py:26` is a module-level
  `defaultdict(list)`. `record_traversal` does list-append +
  list-comprehension rebuild without any lock. `main.py:4265` calls
  `record_traversals([m.id for m in relevant])` from the main thread.
  Current call sites are single-threaded (main loop only). But: as
  soon as pe_chain or any background source calls it (the
  `apply_boredom` path goes via a generic `memories` list), the race
  window opens. Also, the `IGOR_BOREDOM_ENABLED` flag defaults to
  **false** — meaning boredom is currently OFF globally, and the
  feature is dormant. That is itself a finding: a dormant feature
  whose activation would introduce a race condition is a latent bug.
- Blast radius: low today (feature off), medium if enabled without
  fix. Result is not data loss but wrong weight-modifier values
  during concurrent access.
- Biomimicry: the traversal-log-with-decay IS an honest mechanism for
  habituation. The CONCURRENT version is the one we need.
- Proposed ticket:
  - id: T-boredom-lock-and-enable-audit
  - title: Boredom module — add lock around _traversal_log; document enable gate
  - size: S
  - tags: [concurrency, boredom, thread-safety, observability]
  - description: `cognition/boredom.py::_traversal_log` is a
    module-level dict mutated without lock. Gate
    `IGOR_BOREDOM_ENABLED` defaults to false so the race is latent.
    Add `threading.Lock` wrapping append + prune + read, and make
    the enable-gate explicit (docstring + CLAUDE.md mention). Also
    note: this is a second `boredom` concept — distinct from
    `BoredomSource` in `push_sources.py` (which is the arousal-flat
    detector) and `tools/boredom_idle.py` (idle-traversal habit
    tool). Three things called "boredom" doing different work. The
    ticket description should include a 2-sentence "which is which"
    note to prevent future confusion. Scope boundary: do NOT merge
    them — they serve different purposes. Files touched:
    `cognition/boredom.py`, possibly docstring updates. HIGH-inertia
    code touched: none.
  - **Disposal: SHIP.** Tiny, defensive, also documents confusion.

### Finding P1-5.3 — "Sleep consolidation is just clustering"

- Verdict: CONFIRMED_NARROWER. The CURRENT `consolidation.py` is
  clustering + LLM extraction — Pass 1 is right. BUT a separate
  `sleep_consolidation.py` module EXISTS that is closer to the honest
  biology: co-activation edge discovery on `tails` and `traces` logs
  (lines 1–50 of `cognition/sleep_consolidation.py`). The
  just-merged consolidation docstring (lines 82–92) acknowledges this
  split explicitly: "Hebbian co-occurrence edge strengthening NOT
  performed by consolidation.py. Instead, downstream: D154, D233,
  D358, D353 via replay.py." So: Pass 1 is right that
  `consolidation.py` is not Hebbian. Pass 1 missed that
  `sleep_consolidation.py` + `replay.py` ARE doing (or at least
  attempting) the Hebbian work. The architectural honesty is in
  recognizing that both are needed: consolidation = episodic
  abstraction (hippocampal-cortical systems consolidation), sleep
  consolidation = synaptic-trace strengthening (local STDP analog).
  That split IS biologically supported.
- Blast radius: n/a — behavior already present.
- Biomimicry: The SPLIT is honest; the NAMES are misleading.
  `consolidation.py` is really `episodic_abstraction.py` or
  `cluster_extract.py`. Calling both "consolidation" invites the
  confusion Pass 1 fell into.
- Proposed ticket:
  - id: T-consolidation-rename-split
  - title: Clarify: consolidation.py is episodic abstraction, sleep_consolidation.py is the Hebbian half
  - size: S
  - tags: [biomimicry, consolidation, docs, honesty]
  - description: The just-merged consolidation.py docstring explains
    the split correctly. What's missing is surface naming coherence.
    Option A (docs only): add a prominent note at the top of
    consolidation.py that it is NOT sleep consolidation — that lives
    in `sleep_consolidation.py` + `replay.py`. Point each at the
    other. Option B (rename): rename `consolidation.py` to
    `episodic_abstraction.py` since that's what it does. Option A is
    lower-risk. Include a section in the memory palace
    (`theigors/igor/memory`) that lists the 3-way split of
    consolidation mechanisms and which file does what. Scope
    boundary: no code behavior change. Files touched: docstring
    updates, palace node.
  - **Disposal: SHIP** option A only (docs). Rename is too cheap a
    win to be worth the import-site churn.

### Finding P1-1.1 — Silent excepts in daemon_supervisor + self_edit

- Verdict: CONFIRMED. `daemon_supervisor.py:83` (healthy = False on
  exception — reasonable), `daemon_supervisor.py:183` (`log.debug` on
  poll error — DEBUG is too quiet for the safety watchdog), lines
  162-168 (nested try/except logging SILENT_EXCEPT from the original
  SILENT_EXCEPT handler — a matryoshka), `self_edit.py:73`,
  `self_edit.py:102`, `self_edit.py:131` all log at WARNING. The
  consolidation.py bare-excepts at lines 196, 211, 338 log at
  warning — reasonable. Main risk: the supervisor's own poll loop
  can silently fail at DEBUG level. If the supervisor dies, the
  supervised threads continue but are no longer monitored.
- Blast radius: Medium. Silent supervisor death would be invisible
  until a critical thread also died, at which point NO restart.flag
  writes and Igor runs degraded.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-daemon-supervisor-self-heartbeat
  - title: Supervisor poll-loop: log errors at WARNING; add self-heartbeat to main loop
  - size: S
  - tags: [ops, observability, daemon_supervisor]
  - description: `daemon_supervisor._poll_loop` catches exceptions at
    DEBUG level. That's too quiet for the system's own watchdog.
    Change to WARNING. Separately: the supervisor has no heartbeat of
    its own — if the poll thread dies, nothing detects it. Add a
    timestamp: `supervisor._last_poll_ts` set at top of each tick.
    The main loop periodically checks: if `now - last_poll_ts >
    3*poll_interval`, log SUPERVISOR_STALL and attempt to restart the
    poll thread. Scope boundary: do NOT change the dead-thread
    detection logic. Files touched: `daemon_supervisor.py`,
    `main.py` (one check in the main loop). HIGH-inertia code
    touched: none (main.py is MEDIUM, minimal surface change).
  - **Disposal: SHIP.** The supervisor IS Igor's in-process
    watchdog. It deserves a meta-watchdog.

---

## Pass 1 gaps (findings Pass 1 missed in your area)

### Gap 1 — env_sync can poison Igor's safety flags via graph write

- Severity: critical
- Biomimicry: n/a (infrastructure)
- Evidence: `wild_igor/igor/env_sync.py:174-208`. `push_vars_to_graph`
  upserts env vars (except credentials) as FACTUAL engrams.
  `hydrate_from_graph` reads them back into os.environ. The
  credential-skip-list in `_CREDENTIAL_WORDS` does NOT include any
  of the safety flag names (TIER5/ARBITER/SELF_EDIT_ENABLED). So if
  anything writes `SYSCFG_IGOR_TIER5_ENABLED` with
  metadata.env_value="true", the next boot hydrates that into
  os.environ, which then passes `os.getenv(...).lower() in
  ("true","1","yes")`. This was addressed under Finding P1-8.1's
  proposed ticket T-safety-gates-above-env-sync.
- Proposed ticket: see T-safety-gates-above-env-sync above.
- **Disposal: SHIP** (already included under Finding P1-8.1).

### Gap 2 — ExperimentCascade "high-stakes → high-novelty" policy is a safety inversion

- Severity: medium-high
- Biomimicry: theatrical. Real biology does dial up exploration under
  novelty, but not under HIGH-STAKES — that's the inverse. Under
  high stakes, biology exploits known-good responses (freeze, flee,
  fight — each ONE is the cheapest known action). Exploration under
  stress is pathological (overthinking, choking).
- Evidence: `cognition/experiment_cascade.py:770-810` — the
  `_filter_by_predictor` method. Under `is_high_stakes(situation)`,
  it deliberately DOES NOT skip low-confidence levels and REORDERS
  by information gain DESCENDING (line 792). The docstring explicitly
  says: "Under high stakes: explore, don't exploit. Reorder by info
  gain; don't skip any level — we want maximum learning per attempt,
  not fastest match. Biology: dopaminergic novelty bonus is dialed
  up under stress, exploration rate increases."
  This is a misreading of the biology. Dopaminergic novelty bonus is
  dialed up under NOVELTY, not STAKES. Under stakes, the organism
  narrows options and picks the best-predicted one. Moreover: from
  an AI safety framing, a system that explores MORE when stakes are
  higher is the opposite of what you want — high stakes is where
  you want the best-characterized response path.
- Proposed ticket:
  - id: T-engineered-failure-policy-review
  - title: Audit is_high_stakes policy — exploration-under-stakes is biologically inverted
  - size: M
  - tags: [biomimicry, safety, experiment_cascade, engineered_failure]
  - description: `ExperimentCascade._filter_by_predictor` inverts the
    usual predictor-skip behavior under high stakes, preferring
    low-confidence probes. Docstring cites "dopaminergic novelty
    bonus." The citation conflates novelty (curiosity-driven
    exploration signal) with stakes (outcome-criticality signal).
    Biology: high stakes narrow to best-predicted response; novelty
    dials up exploration. Proposal: read the T-engineered-failure-
    experiments design thread, clarify what "high stakes" actually
    means in the cascade context. If the intent was "I'm uncertain
    and this matters, so I should learn fast" — that's really
    high-novelty-AND-high-stakes — the current code is right for
    that. If the intent was just "this matters" — the code is
    inverted. Likely outcome: tighter definition of is_high_stakes
    to mean "high stakes AND high uncertainty"; under
    high-stakes-AND-low-uncertainty, exploit the best-known path.
    Scope boundary: does NOT remove the exploration mode. Only
    narrows when it activates. Files touched:
    `cognition/engineered_failure.py` (is_high_stakes), possibly
    `cognition/experiment_cascade.py` docstring.
  - **Disposal: INVESTIGATE.** Possibly CONFIRMED_WORSE if the
    intent review lands where I think it does. Worth the design
    pass before shipping.

### Gap 3 — MilieuSource force-ticks on every cycle, independent of interaction

- Severity: low
- Biomimicry: honest (constant time decay is correct); but the timing
  interacts with the global-sync contribution subtly.
- Evidence: `push_sources.py::MilieuSource.push:967-984`. Every 60s
  the source calls `m.tick()` — natural decay toward neutral. tick()
  in turn does `_contribute_to_global(s, GLOBAL_ALPHA_ROUTINE)`. So
  every 60s, EVERY running Igor instance contributes its state to
  the shared global milieu file — and each instance periodically
  pulls from it (`GLOBAL_SYNC_TICKS=10` → every ~10 minutes). At
  equilibrium this is fine, but on startup of a second instance
  with a stale local state, the first instance's tick() overwrites
  the shared global with the first's view BEFORE the second reads
  from it. Race is benign (EMA blending), but worth documenting.
- Proposed ticket: (merge with T-milieu-honesty-consolidate) — add a
  docstring note about the cross-instance timing.
  - **Disposal: DISCARD** (fold into T-milieu-honesty-consolidate —
    too small to stand alone).

### Gap 4 — Multiple modules named "boredom" confuse the substrate

- Severity: low (developer confusion more than runtime bug)
- Biomimicry: n/a (naming).
- Evidence: three distinct "boredom" modules:
  1. `cognition/boredom.py` — traversal-log habituation (node-level).
  2. `cognition/push_sources.py::BoredomSource` — milieu-arousal-flat detector.
  3. `tools/boredom_idle.py` — idle-traversal tool (PROC_BOREDOM_TRIGGER).
  Different timescales, different inputs, different outputs, all
  called "boredom."
- Proposed ticket:
  - id: T-boredom-naming-clarification
  - title: Clarify 3-way boredom split in palace and module docstrings
  - size: S
  - tags: [docs, boredom, clarity]
  - description: Three modules named "boredom" do three different
    things. Add a paragraph to each module's docstring distinguishing
    it from the other two, and a palace node
    (`theigors/igor/cognition/boredom`) that links all three.
    Scope boundary: names DON'T change (too much churn), only docs.
    Files: all three boredom module docstrings, one palace node.
  - **Disposal: SHIP** (trivial, prevents future misreads).

### Gap 5 — Interruptors swallow all exceptions, have no own watchdog

- Severity: low-medium
- Biomimicry: these are procedural by design (they're alert routers,
  not cognition). The issue is operational.
- Evidence: `cognition/interruptors.py::run_all:325-339`. Each
  interruptor's `check()` is wrapped in a broad except at WARNING
  level. A broken interruptor logs once per call and keeps going.
  But `run_all` itself has no "number of broken interruptors" counter
  — the system silently runs with a degraded alert path. Also, no
  registration via daemon_supervisor — interruptors run inside the
  main tick loop, so if THAT dies, the supervisor doesn't know why.
- Proposed ticket:
  - id: T-interruptor-health-tracking
  - title: Interruptor health: count consecutive failures, push MILIEU_STRESS on degradation
  - size: S
  - tags: [ops, interruptors, observability]
  - description: `run_all` in `interruptors.py` catches all
    exceptions from each interruptor with no degradation tracking.
    Add a per-interruptor consecutive-failure counter; on >= 3
    consecutive failures, push a high-salience TWM marker
    (INTERRUPTOR_DEGRADED) and include in the daemon_supervisor
    report. Scope boundary: does NOT change what each interruptor
    does. Files: `interruptors.py`. Dead-code check:
    BudgetInterruptor, ContextInterruptor, MilieuInterruptor,
    DiskInterruptor are all active.
  - **Disposal: DEFER.** Nice-to-have; the interruptors themselves
    are pretty safe modules.

### Gap 6 — Milieu's _contribute_to_global uses OS file locking across machines

- Severity: medium (if cross-machine global milieu ever activates)
- Biomimicry: n/a.
- Evidence: `milieu.py::_contribute_to_global:296-323`. Uses
  `fcntl.flock` / `msvcrt.locking` on `milieu.json.lock`. That
  works for same-machine co-located instances. If
  `IGOR_GLOBAL_MILIEU_URL` is set and the global milieu lives on a
  remote machine, the flock does NOT synchronize across machines
  (fcntl is kernel-local). The HTTP path (`_push_to_remote`)
  bypasses the lock entirely, which is correct for that path — but
  if an instance is BOTH a local filesystem contributor AND has
  IGOR_GLOBAL_MILIEU_URL set, the two paths can race.
- Proposed ticket:
  - id: T-milieu-global-mode-exclusivity
  - title: Milieu global contribution: enforce URL-XOR-filesystem mode
  - size: S
  - tags: [milieu, ops, cross-instance]
  - description: If `IGOR_GLOBAL_MILIEU_URL` is set, the remote
    contribution is the source of truth; the local file-based
    `_contribute_to_global` should be a no-op (or write a
    local-only debug copy). Enforce this in `milieu.py`. Scope
    boundary: does NOT change either path individually. Files:
    `milieu.py`. HIGH-inertia: no.
  - **Disposal: DEFER.** Cross-machine global milieu is not
    currently in use; ticket when it is.

### Gap 7 — Gate primitive evaluator fails OPEN (should fail CLOSED for safety gates)

- Severity: medium-high
- Biomimicry: procedurally correct, safety-backwards.
- Evidence: `gate_primitive.py::evaluate_gate:92-95`. When a gate's
  custom evaluator throws, the code returns `(False, "evaluator_error:
  ...")` — False meaning "don't gate." For gates whose purpose is to
  BLOCK unsafe actions (the action_claim_verifier class of gate), this
  is fail-open: if the check crashes, the unsafe action proceeds.
  The comment literally says "fail open."
  For SAFETY gates (CP1-6 defined as gates; future tier-check gates;
  action-claim gates), the correct default is fail-closed: if you
  can't verify, don't act.
- Proposed ticket:
  - id: T-gate-fail-mode-by-domain
  - title: Gate evaluator: fail-open vs fail-closed must be declared per gate
  - size: S
  - tags: [safety, inhibition, gate_primitive, biomimicry]
  - description: `gate_primitive.evaluate_gate` defaults all gate
    evaluator errors to fail-open. That's safe for non-safety gates
    (curiosity, exploration) but wrong for safety gates. Add a
    `fail_mode` field to gate metadata: "open" or "closed". Safety
    gate domains (`action_claims`, `coherence`, `tier_approval`,
    `scope_guard`) default to fail_closed; others fail_open as
    today. Scope boundary: does NOT change any currently-deployed
    gate's behavior (no safety gates exist yet in the graph — only
    the standalone stopgap modules). Prepares for when the pattern
    primitive migration lands. Files: `gate_primitive.py`, one test.
  - **Disposal: SHIP.** Small, forward-looking, prevents a future
    silent-fail on a safety-critical migration.

### Gap 8 — `scope_guard.run_scope_guard` runs twice on a single basket

- Severity: low-medium (correctness, duplicate side effect)
- Evidence: `scope_guard.py:207-229` (first loop over hypotheses) and
  `scope_guard.py:230-281` (second pass that also checks the primary
  target). If the primary target is HIGH-inertia, it gets escalated
  twice, potentially double-posting the DESIGN PROPOSAL message and
  double-calling `cc_queue.py propose`. The ring audit entry is
  also written twice. The first loop `return _pe_esc(basket, reason)`
  should prevent falling through — verify. Reading again: yes, the
  first loop RETURNS on HIGH match, so the second block is
  unreachable for HIGH. OK, not a duplicate-escalation bug. But the
  structure IS genuinely confusing — the second block duplicates
  the tier classification logic. Refactor opportunity, not a
  correctness issue.
- Proposed ticket:
  - id: T-scope-guard-simplify-control-flow
  - title: scope_guard.run_scope_guard — simplify two-loop structure
  - size: S
  - tags: [refactor, scope_guard, clarity]
  - description: `run_scope_guard` has a loop over all hypotheses
    that returns on HIGH inertia, followed by a second block that
    re-classifies the first hypothesis. The second block is
    unreachable for HIGH (first loop returned) but still runs for
    MEDIUM and LOW. Refactor into a single pass that collects
    (tier, hyp) tuples and processes the set once. Not a
    correctness fix — a clarity fix. Files: `scope_guard.py`.
  - **Disposal: DEFER.** Cosmetic.

---

## Dead-code cross-check

- Habits referencing non-existent code in your area: **likely none live
  in DB but PROC_BOREDOM_TRIGGER was documented in past sessions with
  `code_ref=tools.boredom_idle:run_boredom_check`** — verify the
  target still exists: YES,
  `wild_igor/igor/tools/boredom_idle.py::run_boredom_check` at line
  195 is present. Confirm the habit itself exists via `habit_list`
  at runtime.
- Habits in our area that likely exist: `PROC_CONSOLIDATION` (planned
  per docstring), `PROC_BOREDOM_TRIGGER`, `PROC_WORKER_FOREMAN` (via
  BoredomSource comment), `PROC_CODING_SPRINT`, `PROC_ADOPT_GOAL`
  (via scope_guard docstring). Runtime check via `habit_list` tool
  is the honest way to confirm — Pass 2 is static-only.
- Code in your area not referenced by any habit or test: **likely
  orphans:**
  - `gate_primitive.py` — defines the primitive but no habit in the
    DB yet uses `gate: true` metadata. This is the "built-for-future"
    class. Not a delete candidate; note as "awaiting first
    deployment."
  - `inhibition_chain.py::InferenceCheckNode`,
    `EstimateCheckNode`, `ActionGateNode` — stubs that always return
    False. These are intentional placeholders per the docstring.
    Note but don't delete.
  - `experiment_cascade.py::_StubLevel` for level 3 — stub.
    Intentional.

---

## What else? (remit section)

### What should we be asking?

- Does the milieu actually DRIVE behavior, or is it ornamental? The
  honest path is the arousal-lowers-threshold coupling in
  basal_ganglia — that IS load-bearing. Confirm by forcing arousal to
  0.9 in a test fixture and verifying habit firing rate increases.
  If it doesn't, milieu's honesty is an aspiration, not a reality.
- What's the REAL load-bearing rate of habit misfire? No central
  counter (hence T-misfire-taxonomy-aggregator). Without that
  number, we're tuning by anecdote.
- Where is the "refractory period" primitive? Multiple modules
  reinvent it (gate_primitive's TTL, verifier cooldowns,
  interruptor cooldowns, BoredomSource cooldown). One primitive
  would centralize the concept.

### How can we help him learn and reason better?

- **Honestify the sensor upstream.** Milieu is honest but
  `update(valence, friction, roi)` is fed by PFC numbers that are
  themselves assessments. The biomimetic dream is that friction is
  SENSED, not computed. InteroceptionSource is the right shape;
  extend it upstream so milieu responds to honest signals more often
  than procedural ones.
- **Wire the verifier signals to milieu.** A COHERENCE_FAILURE or
  CONFAB_CAUGHT should nudge dominance down slightly. Currently the
  verifier pushes TWM but doesn't close the loop on affect. That's a
  missed biomimetic opportunity — self-caught error is a
  dominance-shaping signal.
- **Give the arousal-climbing gradient a canonical response engram.**
  `is_arousal_climbing` is computed, a MILIEU_REGULATE TWM entry is
  pushed, but the consumption path is opaque. An explicit
  PROC_REGULATE_AROUSAL habit (breath-analog: slow down, close
  tabs, clear stale TWM) would make the loop visible.

### Small-hardware optimizations

- The `milieu` ring buffer, global-sync logic, and four update
  methods together run every 60s per instance. On a small machine
  running 3 instances, that's 180 file-opens per minute on
  `milieu.json` + lock file. LISTEN/NOTIFY via Postgres (area 8's
  ticket) would eliminate the file-system thrash.
- `daemon_supervisor._poll_loop` runs every 5s forever. On a quiet
  machine that's pure overhead. Adaptive poll interval — 5s when a
  thread has recently died, 30s when everything's been stable for an
  hour — would cut background CPU by >80%.
- `env_sync.boot_env_sync` does max-mtime of all cfg files on every
  boot. Fine at startup. If anything ever calls it in a hot path,
  that's N stat() calls. Verify call site is boot-only.

### Engram review process for our area

- **Gates are engrams.** When gate_primitive + pattern primitive
  migration land, the coherence and action-claim detectors become
  PROCEDURAL nodes with `gate: true`. Those nodes NEED the same
  audit treatment — the multi-persona pass /audit-engrams sketched
  in Pass 1 section 12. For our area specifically: every gate
  engram should declare its `fail_mode` (see Gap 7).
- **Scope tiers should be data, not code** (see
  T-scope-guard-inertia-from-graph). Once they are data, the engram
  audit covers them too.

### CC-workflow touchpoints (for area 9 to integrate)

- Every HIGH-inertia edit goes through scope_guard → _pe_escalate →
  cc_queue propose → manual CC approval. That path is load-bearing
  and currently ad-hoc (channel message + cc_queue.py CLI
  invocation). A skill `/approve-design-proposal <ticket>` would make
  the CC side symmetric with Igor's side.
- Daemon supervisor status should be surfaced in `/day-close-audit`
  (it is — `report_str()` is specifically for that, per the
  docstring). Confirm at runtime.
- The `restart.flag` path is a coordination primitive between
  daemon_supervisor and main.py. A mis-placed restart.flag (wrong
  instance dir) would silently not trigger. A pre-commit hook that
  checks restart.flag paths stay under `paths().instance` would
  prevent drift.

---

## Summary

- Ticket candidates total: **17** (15 unique, plus 2 sub-variants
  under scope_guard dedup).
- Recommended SHIP: **10**
  1. T-milieu-honesty-consolidate
  2. T-safety-gates-above-env-sync (highest stakes)
  3. T-scope-guard-dedup-with-self-edit
  4. T-daemon-supervisor-backoff-and-one-shot-audit
  5. T-dominance-threshold-spiral-guard
  6. T-verifier-refractory-window
  7. T-boredom-lock-and-enable-audit
  8. T-consolidation-rename-split (docs only)
  9. T-daemon-supervisor-self-heartbeat
  10. T-boredom-naming-clarification
  11. T-gate-fail-mode-by-domain
- Recommended DEFER: **5**
  - T-scope-guard-inertia-from-graph (DEFER — graph-derived design)
  - T-misfire-taxonomy-aggregator (DEFER — downstream consumer undesigned)
  - T-interruptor-health-tracking (DEFER — nice-to-have)
  - T-milieu-global-mode-exclusivity (DEFER — feature not in active use)
  - T-scope-guard-simplify-control-flow (DEFER — cosmetic)
- Recommended INVESTIGATE: **3**
  - T-goal-anchor-salience-floor (INVESTIGATE — needs trace data)
  - T-tool-latency-signal-to-milieu (INVESTIGATE — may already be
    partially implemented)
  - T-engineered-failure-policy-review (INVESTIGATE —
    design-intent verification before ticket)
- Recommended DISCARD: **1**
  - Gap-3 standalone ticket — folded into T-milieu-honesty-consolidate.
- **Highest-stakes single finding in this area:**
  **T-safety-gates-above-env-sync** — three safety flags
  (IGOR_TIER5_ENABLED, IGOR_ARBITER_ENABLED,
  IGOR_SELF_EDIT_ENABLED) propagate through env_sync.py to/from the
  graph. A graph-write path (via cortex.store of a SYSCFG_* node
  with updated env_value metadata) flips the flag on next
  boot_env_sync. The scope_guard + self_edit sandbox is designed
  to prevent FILE writes to these gates; nothing prevents GRAPH
  writes. This is the plausible route by which Igor's own cognition
  could flip its own safety gates.
- **Top biomimicry-honesty-call:** Pass 1's claim that milieu is
  honest is **CONFIRMED** — it is genuinely the most biomimetic
  affective module in the codebase. The reservations are upstream
  (`update()` takes pre-computed PFC numbers; InteroceptionSource
  is the honest sensor path, extend it) and downstream (the
  `_compute_threshold`'s dominance-raises-threshold term can spiral
  without a recovery bonus — T-dominance-threshold-spiral-guard
  addresses this). Pass 1's additional claim that the
  arousal→threshold coupling makes corrective habits HARDER to
  fire under stress is **REFUTED** — that's the dominance term, not
  the arousal term, and Pass 1 mis-stated the sign on arousal.

### One sentence for Pass 3

Please decide whether the two-tier inertia plan (SHIP
T-scope-guard-dedup-with-self-edit now, DEFER
T-scope-guard-inertia-from-graph until graph-derived config lands) is
the right cadence, and confirm that T-safety-gates-above-env-sync is
the single must-ship safety ticket from this area before any further
IGOR_SELF_EDIT_ENABLED experimentation.
