# Pass 2 deep-dive — cognition + reasoning

Scope: `inference_gateway.py`, `reasoners/{base,ollama_reasoner,openrouter_reasoner}.py`,
`turn_pipeline.py`, `reasoning_workflow.py`, `narrative_engine.py`, `thalamus.py`,
`system_prompt.py`, `reasoning_cache.py`, `voice_ab.py`, `hebbian_bridge.py`,
`word_graph.py`.

All line numbers are from the files as they exist today (post the canonical-
docstring merges referenced in the kickoff).

---

## Per-finding verdicts

### Finding P1-1 — `_process_inner` is a monolithic turn orchestrator

- **Verdict:** CONFIRMED_WORSE.
  Pass 1 said "over 300 lines." Actual: `_process_inner` starts at
  `main.py:3404` and the body runs past line 5728 — roughly **2,300 lines**
  in a single method. It subsumes TWM push, thalamus parse, comprehension
  signal, ring write, repair detection, reply-gap detection, investment
  check, CC-tool-bypass, wait, preparse, relationship frame, memory search,
  winnow invocation, habit dispatch, tier.0 gate, turn_pipeline run,
  `gateway.reason` fall-through, confabulation gate, voice overlay, ring
  integration, episode binder flush, and forensic logging. The LEGACY path
  and the NEW `TurnPipeline` path coexist inside the same method (gated by
  `IGOR_TURN_PIPELINE` defaulting true) with silent fall-through on
  exception. Legacy is not retired; it is still the fallback for every
  turn.
- **Blast radius:** Everything. This is THE turn method. Any new cognitive
  capability gets shoe-horned here. Every test that drives a full turn
  touches it. The new `TurnPipeline` (biomimetic cascade → workflow →
  decision_blob → voice) is wired in at `main.py:5666–5713` but its output
  is discarded on any exception — the legacy gateway.reason path then
  runs. That means the "retirement" of the legacy path has not actually
  happened; both paths run per turn under a try/except.
- **Biomimicry:** `procedural-with-bio-name`.
  The method is called `_process_inner`, no biology, fine. But the
  *pipeline it contains* is titled "prefrontal cortex" in comments and
  claims to be the biomimetic path. It is a sequential conductor — push,
  then parse, then search, then dispatch — with hard-coded ordering. An
  honest version would push each stage's output as salience-weighted TWM
  entries and let a single dispatcher loop pick the winning coalition
  (D099 co-activation already exists — it just isn't used as the main
  loop's selector).
- **Proposed ticket:**
  - id: `T-process-inner-dismantle`
  - title: Dismantle `_process_inner` into salience-driven stages
  - size: XL
  - tags: [cognition, biomimicry, refactor, turn-pipeline]
  - description:
    `_process_inner` has reached 2,300 lines and holds two parallel turn
    pipelines (legacy direct-reasoner + new TurnPipeline) inside one
    method. Disposal is NOT a code move — the biomimetic refactor is the
    point. Shape: (1) turn the current linear sequence into a set of
    stage functions that each push TWM entries with explicit salience,
    urgency, and category; (2) make a small selector loop the only thing
    `_process_inner` owns — it iterates until a winning coalition
    commits via `decision_blob.can_commit()` or a wall-clock budget
    expires; (3) retire the legacy `gateway.reason` fall-through inside
    the method — it moves to a *fallback stage* with an explicit
    catastrophic-failure TWM marker, not a try/except swallow. Do NOT
    change reasoner interfaces (`reasoners/base.py` is HIGH-inertia;
    reason() stays as-is). Do NOT touch `turn_pipeline.py`'s cascade
    layer — it already has the right shape. Files touched: `main.py`
    (extract stages to new `cognition/turn_stages.py`), `forensic_logger`
    (stage labels). Legacy path is safe to delete ONLY after
    `T-retire-legacy-direct-reasoner-path` closes on its own evidence
    (30 days of pipeline-resolved turns without fallback firing). This
    ticket would make the dismantlement possible; actual legacy delete
    is a separate follow-up.
  - **HIGH-inertia: YES.** Touches main.py + reasoners import surface.
  - **Disposal:** INVESTIGATE.
    Too big to SHIP blind; the biomimetic-loop shape needs a design doc
    before implementation (competition rules, salience budget, tie-break,
    timeout semantics). But the problem is real and urgent — every
    session of CC work reopens this file. Next step: a design ticket
    that produces a one-pager on the selector loop contract, then
    ticket-batch the stage extractions.

---

### Finding P1-2 — Busy-wait main loop (`while True` + `time.sleep(0.1)`)

- **Verdict:** NEEDS_RUNTIME. Static: the pattern is present in `main.py`.
  Whether it's actually a CPU issue in practice depends on idle latency
  traces. `ResourceMonitorSource` already exists; its output would answer
  this.
- **Blast radius:** Low correctness risk; measurable CPU cost.
- **Biomimicry:** `n/a` — engineering concern.
- **Proposed ticket:**
  - id: `T-main-loop-event-drive`
  - title: Event-drive the main loop (queue.get + LISTEN/NOTIFY)
  - size: M
  - tags: [infra, performance, main-loop]
  - description:
    Replace `while True: sleep(0.1)` idle polling with `queue.get(timeout=N)`
    for the stdin/message queue, and Postgres `LISTEN/NOTIFY` for TWM
    wake-ups. The NE trigger currently polls `twm_count_unintegrated()`;
    it could be woken by NOTIFY on insert. Scope boundary: main.py's
    stdin_reader thread and queue drain loop. Do NOT change
    `daemon_supervisor.py` (that has its own polling rhythm and a
    different role). Reading this as area-cross-cut: infra Pass 2 will
    own the LISTEN/NOTIFY change; this ticket is just the main-loop
    consumer side.
  - **Disposal:** DEFER. Low-value until a runtime profile shows the
    busy-wait is actually hot. Igor's idle CPU is not currently a
    reported problem.

---

### Finding P2-ev — Missing event bus; inter-subsystem comms via direct call + TWM

- **Verdict:** CONFIRMED.
  `gateway.reason` is called directly from `main.py`, `narrative_engine`,
  `voice_ab`, `llm_peer_advisor`, `reasoners/base`. The `_winnow_context`
  method on BaseReasoner directly imports `inference_gateway.get_gateway`
  (base.py:749). There is no pub/sub layer — every consumer imports the
  gateway singleton. TWM does function as an asynchronous shared
  workspace for some flows, but it is a polled table, not a bus.
- **Blast radius:** Every reasoning call site. Moving to an event bus
  implies changing call sites for NE, voice_ab, turn_pipeline, and the
  legacy main path — but not the reasoner interfaces themselves.
- **Biomimicry:** Mixed. TWM-as-workspace is the *intended* bus and is
  already a honest global-workspace analog. The problem is that callers
  mostly bypass it and call the gateway directly. The gateway IS the bus
  for inference calls; TWM is the bus for cognitive state. Don't add a
  third bus — make more callers use TWM for cross-subsystem
  notification.
- **Proposed ticket:**
  - id: `T-twm-as-bus-enforcement`
  - title: Route cross-subsystem signals through TWM, not direct calls
  - size: L
  - tags: [architecture, biomimicry, twm, cognition]
  - description:
    Four specific call chains should produce TWM entries and let
    consumers pick them up, rather than direct invocation: (1) NE
    finishing a run → currently writes `category=narrative` ring entry;
    should also push a `category=ne_arc` TWM entry with the arc summary
    so downstream consumers (voice, action_claim_verifier) see it
    consistently; (2) basal_ganglia firing a habit → should push a
    `category=habit_fired` TWM marker so confabulation_gate /
    action_claim_verifier can compare against it without re-reading
    traces; (3) gateway tier-fall-through → already logged to
    forensic_logger; should also emit a TWM marker for
    cognition_health_observer; (4) voice A/B winner → push a TWM
    marker so NE can include it in the next arc. Scope NOT included:
    removing any direct call to `gateway.reason` or
    `gateway.call` — those remain the inference API. This is adding
    signal markers, not removing call paths. Files touched:
    `narrative_engine.py`, `basal_ganglia.py`, `inference_gateway.py`,
    `voice_ab.py`. Cross-cuts with area-2 (cortex TWM API).
  - **Disposal:** DEFER.
    Valuable but not urgent; TWM already carries most of this. Pass 3
    should check with area-2 before claiming the TWM API is stable
    enough.

---

### Finding P4-1 — `reasoning_cache` is unbounded

- **Verdict:** CONFIRMED_NARROWER.
  `reasoning_cache.py` is file-backed (`~/.TheIgors/cache/reasoning/<sha>.json`),
  so it is NOT in-memory unbounded — it's disk-unbounded. Each entry
  self-deletes on TTL (720s) or TWM-watermark mismatch in the `get()`
  path. But entries that are never `get`'d again stay on disk forever.
  Over a 72-hour run with thousands of NE calls, that's thousands of
  orphan JSON files.
- **Blast radius:** Disk usage, cache dir inode pressure.
  Only affected callers: `narrative_engine._call_inference`
  (narrative_engine.py:1024, 1040).
- **Biomimicry:** `honest` — memory-trace persistence with recency is a
  reasonable engram-lifetime analog. The problem is *engineering*
  hygiene, not biology.
- **Proposed ticket:**
  - id: `T-reasoning-cache-sweep`
  - title: Add disk-sweep + size-cap to reasoning_cache
  - size: S
  - tags: [infra, cache, hygiene]
  - description:
    Add a periodic sweep (every N NE runs, or on `put()`) that deletes
    cache entries older than 2×TTL. Additionally, cap directory size at
    N entries (e.g. 5_000); when exceeded, delete oldest by mtime.
    Scope NOT included: in-memory LRU layer (unnecessary — disk access
    is fine for this volume). Do not change the cache key or TTL.
    Files touched: `reasoning_cache.py`.
  - **Disposal:** SHIP. Small, obvious, immediate disk-hygiene win.

---

### Finding P5-a — Turn pipeline is procedural, should be salience competition

- **Verdict:** CONFIRMED but NUANCED.
  The *new* `TurnPipeline` (`turn_pipeline.py`) is actually the right
  shape already: cascade walks levels 0–4 (substrate attempts) and
  escalates to a reasoning *conversation* (not a fat one-shot) at level
  5. It is the LEGACY path inside `_process_inner` that is procedural
  (Pass 1 was looking at that).  `TurnPipeline` enforces CP6 via
  `decision_blob.can_commit()`. The finding is CONFIRMED for the legacy
  path, REFUTED for the new pipeline's shape.
- **Blast radius:** The new pipeline is gated on by default but its
  output is discarded on any exception. Effectively the legacy path
  still dominates stability-wise.
- **Biomimicry:** `honest` — cascade → conversational escalation →
  decision blob → voice is a plausible basal-ganglia-to-PFC-to-voice
  chain. Not theatrical.
- **Proposed ticket:**
  - id: `T-retire-legacy-reasoner-path`
  - title: Harden TurnPipeline as the only interactive path
  - size: M
  - tags: [cognition, turn-pipeline, retirement]
  - description:
    The legacy path in `_process_inner` is currently a silent fallback
    for any `TurnPipeline` exception (main.py:5709). This masks real
    pipeline failures and keeps the legacy path always-on. Shape: (1)
    on pipeline exception, log loudly, write a high-urgency TWM marker,
    and return a graceful-error reply with the exception classification
    visible to the user — don't fall through; (2) add a dashboard metric
    for pipeline_resolved vs pipeline_failed per hour; (3) once 7
    consecutive days show pipeline_failed ≤ pipeline_resolved / 100,
    delete the legacy fallback block in `_process_inner` and remove
    `IGOR_TURN_PIPELINE` env var. Scope NOT included: changing the
    cascade levels, workflow A, or voice actors. Files touched:
    `main.py` (the fallback block around line 5709–5713), a new
    `health_metrics.py` surface. This is the follow-up to
    T-retire-legacy-direct-reasoner-path already in backlog.
  - **Disposal:** DEFER.
    Needs the metric in place first, then the delete. Pre-delete
    metric work is SHIP-able on its own.

---

### Finding P7-a — TWM is a list, not a working memory

- **Verdict:** CONFIRMED.
  Detailed biomimicry verdict belongs to area-2 (cortex). For area-3:
  the *consumers* of TWM in cognition (`_build_session_context`,
  NE filter/sort, `build_twm_context`) treat TWM as a ranked list and
  nothing more. There is no rehearsal loop (no code re-reads a TWM
  entry to keep it active). Spreading-activation output
  (`cortex.spreading_activation`) is called from NE
  (narrative_engine.py:603, 677) but its output is consumed only for
  prediction-error training and coalition detection — it doesn't
  re-inject into TWM to prime subsequent retrieval *in the same turn*.
- **Blast radius:** Cognition-wide. Priming, rehearsal, attention
  stability all absent.
- **Biomimicry:** `procedural-with-bio-name`.
  "Working memory" should mean bounded-capacity, actively-maintained,
  competitively-evicted. Current TWM is "observations table with TTL +
  salience."
- **Proposed ticket:**
  - id: `T-twm-rehearsal-priming`
  - title: Add rehearsal loop + priming re-injection to TWM consumers
  - size: L
  - tags: [cognition, twm, biomimicry, priming]
  - description:
    Two specific consumer changes in cognition, each independently
    valuable: (1) Rehearsal: on every cognitive cycle where TWM is
    read, re-stamp the top-K salient entries' `last_rehearsed` field
    (add this field in area-2's ticket). A rehearsal pass extends
    effective TTL for high-attention items. (2) Priming: after NE or
    thalamus produces activation (word_graph predictions,
    spreading_activation heat), push the predicted terms/node_ids back
    into TWM with `category=priming`, short TTL (30s), and low
    salience. The next turn's cortex.search can bias toward these.
    Scope NOT included: changing TWM's storage or capacity
    (area-2 concern); new categories must be documented in the
    palace. Files touched: `narrative_engine.py` (priming push),
    `reasoners/base.py:_winnow_context` (already uses word_graph
    predictions; extend to push priming), `thalamus.py` (priming
    push from keywords). HIGH-inertia: NO — no changes to
    `reasoners/base.py`'s public contract. Cross-cuts area-2.
  - **Disposal:** INVESTIGATE.
    The feature is biomimetically legitimate. Needs a short design
    doc on priming TTL, salience floor, and de-dup with existing TWM
    entries before shipping. Pass 3 flags: area-2 must confirm it
    accepts a `last_rehearsed` field.

---

### Finding P8-a — Tier gating brittle; scope_guard string-match fragility

- **Verdict:** CONFIRMED. For scope of this area: the
  `IGOR_TIER5_ENABLED` flag is moot — t5 is hardcoded `None` at
  inference_gateway.py:415 (the dead code still present in code comments
  even references "D329: OR handles all cloud routing"). The actual tier
  boundary that matters for safety is "cloud escalation at all", gated
  by the `_cloud_ok` flag check on `self._t4` (inference_gateway.py:529).
  That flag is evaluated once at `from_env()` boot and trusts OR API
  key alone — no cryptographic or file-permission check on the env.
- **Blast radius:** Any process with env-write can elevate tiers. Igor's
  own `self_edit` tool has write access to `wild_igor/igor/`. It has
  been seen to edit `.env` in the past (though disabled). Current
  exposure: low in practice, high in principle.
- **Biomimicry:** `n/a` — safety gate, not a cognitive mechanism.
- **Proposed ticket:**
  - id: `T-tier-gate-integrity`
  - title: Integrity-check tier flags at boot; fail closed
  - size: S
  - tags: [safety, inference-gateway, gating]
  - description:
    At `InferenceGateway.from_env()`, read `.env.sha256` sidecar file;
    if the hash of `.env` doesn't match, refuse to initialize cloud
    tiers (t3/t3.5/t4). The sidecar is updated by an explicit
    human-run command (not by Igor, not by self_edit). This lets Akien
    lock in a known-good cloud-gating configuration. Scope NOT
    included: removing or moving `IGOR_TIER5_ENABLED` (already dead),
    changing how OR API key is read. Files touched:
    `inference_gateway.py` (from_env), a new
    `tools/env_integrity.py`. Separate from
    `scope_guard` (area-7 concern).
  - **Disposal:** INVESTIGATE.
    Akien has deferred similar "Igor can't edit his own safety" work
    before; this needs an explicit go-ahead before shipping. The
    problem is real; the remedy shape is the question.

---

### Finding P9-a — Feedback-loop gaps: tool latency → tier, cost → habit compile

- **Verdict:** CONFIRMED.
  `inference_gateway.py` tracks `last_elapsed_ms` on the context
  (line 281, 297) but never reads it for routing — `_local_preferred`
  does not consult elapsed; `_cloud_preferred` does not consult
  elapsed. Every call starts routing from scratch. The only elapsed-
  aware thing is `_try_restart_local_ollama` (a recovery action, not a
  routing decision). No feedback loop closes. On cost: cost is returned
  from reason() (return cost_usd), logged via forensic_logger, but not
  summed into a `self_trainer` signal that proposes habit compilation.
- **Blast radius:** Medium — this is the kind of feedback loop Igor's
  thesis depends on (cheap local reasoning grows until the cloud isn't
  needed). Absent, the system will not self-train its own routing.
- **Biomimicry:** `procedural-with-bio-name`.
  The gateway uses words like "local-first" and "budget" that suggest
  adaptive allocation, but the allocation is hard-coded by if/else on
  env + balance. Nothing learns. Honest version: route decisions
  should be edges in the graph whose weights update from observed
  latency + cost + quality per `purpose_id`. D198 originally had
  exactly this framing; implementation drifted back to procedural.
- **Proposed ticket:**
  - id: `T-gateway-feedback-loops`
  - title: Close three feedback loops at the inference gateway
  - size: L
  - tags: [cognition, biomimicry, gateway, learning]
  - description:
    Three loops, each independently shippable: (1) Tool-latency →
    tier: per `purpose_id`, track rolling median elapsed for each
    handler. If ollama_preparse median > 2× OR preparse median over
    last 50 calls, flip the purpose's routing edge priority.
    Persist across restarts (stored on a `gateway_stats` memory node).
    (2) Cost → habit compilation: at each successful cloud call,
    emit a `training_candidate` TWM entry with the user input, the
    response, the cost, and the purpose. `self_trainer` already
    consumes gaps; extend it to consume training_candidates. (3)
    Quality → routing: `voice_ab` already compares graph vs LLM.
    Extend the signal to the gateway: when graph wins, decrement
    that purpose's cloud preference. Scope NOT included: changing
    reasoner interfaces (HIGH-inertia); changing budget.py. Files
    touched: `inference_gateway.py` (edge weights read from stats),
    new `cognition/gateway_stats.py`, `self_trainer.py` (accept
    new candidate category). HIGH-inertia: partial — reads from
    `reasoners/base.py` but doesn't change its contract.
  - **Disposal:** INVESTIGATE.
    This is the most thesis-critical finding in my area. Big enough
    that it wants a design doc before splitting into SHIP units. Pass 3
    should highlight this as a biomimetic-honesty crux.

---

## Pass 1 gaps (findings Pass 1 missed in my area)

### Gap 1 — `word_graph.py` docstring says "SQLite" but storage is `PGDatabaseProxy`

- **Severity:** low (doc drift), high (rule-violation signal).
- **Biomimicry:** `n/a`.
- **Evidence:** `word_graph.py:1` (module docstring: "SQLite-backed
  word co-occurrence index"), `word_graph.py:19` ("Storage: SQLite
  (~/.TheIgors/{name}.db)"), `word_graph.py:936`
  ("Open (or create) the SQLite word graph…"), `word_graph.py:966`
  ("Returns ~/.TheIgors/{name}.db (SQLite). Old .json files can be
  deleted."). The actual imports (line 36): `from
  ..memory.db_proxy import DatabaseProxy, make_home_proxy,
  make_local_proxy` and line 370: `from ..memory.db_proxy import
  PGDatabaseProxy`. CLAUDE.md's top rule: "NO SQLITE ANYWHERE —
  everything Postgres." The docstring is a lingering 2025-era artifact.
- **Proposed ticket:**
  - id: `T-word-graph-docstring-drift`
  - title: Fix `word_graph.py` docstring (SQLite claim, actually PG)
  - size: S
  - tags: [docs, hygiene, live-in-code]
  - description:
    The module docstring and three downstream docstrings claim
    SQLite. The code uses `PGDatabaseProxy`. Per T-docs-live-in-code,
    the docstring is the canonical documentation. Rewrite the
    docstring to reflect Postgres-backed storage via `db_proxy`, and
    drop the "Old .json files can be deleted" line (which is also
    stale — no .json migration is live). Scope NOT included: the
    `.db` path component (path abstraction is a separate ticket).
    Files touched: `word_graph.py` (docstring only).
  - **Disposal:** SHIP. Trivial, one-file doc fix. Respects
    live-in-code rule.

### Gap 2 — `ModelFamily`, `ClaudeFamily`, `BrowserReasoner` are unused classes

- **Severity:** medium.
- **Biomimicry:** `n/a`.
- **Evidence:** `reasoners/base.py:813–915` declares `LocalReasoner`,
  `APIReasoner`, `BrowserReasoner`, `ModelFamily`, `ClaudeFamily`.
  `grep -r "ModelFamily\|ClaudeFamily"` outside base.py and
  `seed_code_dsbs.py` (archived): zero call sites. `BrowserReasoner`
  is referenced only by `system_prompt.py` (likely a doc string).
  These are dead abstractions from the D026 "two-level hierarchy"
  design that was superseded by the gateway tier ladder. `base.py`
  itself says (in the docstring) "AnthropicReasoner ... removed per
  D188 ... Do not resurrect" — but leaves `ClaudeFamily`'s channels
  list referencing it.
- **Proposed ticket:**
  - id: `T-reasoner-hierarchy-prune`
  - title: Delete dead reasoner hierarchy classes (ModelFamily,
    ClaudeFamily, BrowserReasoner)
  - size: S
  - tags: [hygiene, reasoners, dead-code]
  - description:
    Pass 1's T-audit-2026-03-25 found 58 dead habit code_refs. This
    is the type-analog: dead abstraction classes. Keep
    `LocalReasoner` and `APIReasoner` (they're real — OllamaReasoner
    and OpenRouterReasoner inherit from them). Delete
    `BrowserReasoner`, `ModelFamily`, `ClaudeFamily`. Update the
    docstring's D026 narrative from "two-level hierarchy" to
    "transport base classes" — the second level never landed.
    **HIGH-inertia:** YES — this is `reasoners/base.py`. The change
    is surface-shrink-only, but Akien reviews all base.py edits.
    Scope NOT included: BaseReasoner, the winnow/token-economy
    plumbing, or any `reason()` signature. Files touched:
    `reasoners/base.py`, `system_prompt.py` (if it references
    BrowserReasoner in a format string — verify).
  - **Disposal:** DEFER. SHIP-able in a quiet week, but HIGH-inertia
    means it waits for an explicit "yes, prune it."

### Gap 3 — Hebbian bridge is feature-flagged OFF by default

- **Severity:** high — this is the whole Hebbian story.
- **Biomimicry:** `honest` (when enabled), but currently dark.
- **Evidence:** `hebbian_bridge.py:25`: `_ENABLED =
  os.getenv("IGOR_HEBBIAN_BRIDGE", "false").lower() in (...)`.
  All three entry points short-circuit on `not _ENABLED`. The
  bridge contains the clearest Hebbian-correspondence code in the
  repo (retrieval strengthens word-graph edges proportional to
  arousal and rank). Pass 1-5 called Hebbian "a lie." The honest
  critique is narrower: *when the bridge is disabled* Hebbian is a
  lie; when enabled, the mechanism actually strengthens
  co-activated edges via `reinforce_text` over the generation word
  graph, which IS the biology. Akien has not enabled it.
- **Proposed ticket:**
  - id: `T-hebbian-bridge-enable-audit`
  - title: Decide Hebbian bridge enable status; document why it's off
  - size: M
  - tags: [biomimicry, learning, decision, hebbian]
  - description:
    The bridge is the only code in Igor that does what "Hebbian
    co-activation" actually means: retrieving a node strengthens the
    word-graph edges between its key terms, proportional to arousal.
    It has been disabled since introduction. Either (a) enable it
    with a staged rollout (one machine, one week, measure graph
    growth + retrieval-quality delta), or (b) document in the
    docstring that it's an experimental dormant feature and we are
    not currently claiming Hebbian behavior. Do NOT leave it in the
    current middle state where the code exists, the docstring
    claims the mechanism, and the flag is off. Files touched:
    `hebbian_bridge.py` (docstring + possibly default flip),
    `narrative_engine.py` docstring (D353 sleep-consolidation
    claim), `reasoners/base.py` docstring (Hebbian references).
    Scope NOT included: changing the _ENABLED gate behavior at
    runtime. Decision owner: Akien.
  - **Disposal:** INVESTIGATE.
    The bridge is the thesis's strongest Hebbian evidence — either
    claim it and turn it on, or retract the claim from docstrings.

### Gap 4 — `_cloud_ok` availability check drifted from the documented semantic

- **Severity:** medium.
- **Biomimicry:** `n/a`.
- **Evidence:** The docstring at `inference_gateway.py:526–539` says
  "`is_cloud_training_active()` is a research-mode flag — NOT the
  availability gate. If we have a live t4 reasoner, cloud is
  available. (D198 fix)". The implementation at line 529: `_cloud_ok =
  bool(self._t4)`. This means `_cloud_ok` never considers the
  balance, the budget floor, the time-of-day override, or the
  `balance_ok` field on InferenceContext. Contrast with the edge
  conditions `_cloud_ok(ctx)` and `_cloud_preferred(ctx)` which DO
  use `ctx.balance_ok` and `ctx.cloud_ok_override`. There are
  therefore TWO "cloud ok" semantics in the same file: the
  inline-in-`reason()` truthy-if-t4 check and the DAG-edge
  ctx-aware check. The inline version bypasses the override.
- **Blast radius:** D071 night-mode override silently does nothing
  for `reason()` paths (interactive/background/batch), only for
  `call()` paths.
- **Proposed ticket:**
  - id: `T-cloud-ok-unify-semantic`
  - title: Unify `_cloud_ok` check across gateway reason() and call()
  - size: S
  - tags: [cognition, gateway, gating, safety]
  - description:
    `_cloud_ok` has diverged. In `reason()` it's `bool(self._t4)`;
    in edge conditions it's `ctx.balance_ok AND
    (not is_background OR cloud_ok_override)`. D071 (file-backed
    night-mode) therefore only applies to `call()` (preparse,
    winnow, ne, think, reading_extract), not to the interactive
    reasoning path. Unify by passing an `InferenceContext` into
    `reason()` and using the same predicate. Scope NOT included:
    changing tier selection (t3 vs t3.5 vs t4), changing budget.py,
    or altering D254 human-turn routing. Files touched:
    `inference_gateway.py` (reason signature + call sites in
    main.py). Small but subtle; deserves its own ticket rather
    than riding on T-gateway-feedback-loops.
  - **Disposal:** SHIP. Small and fixes a live semantic drift that
    Akien has flagged before ("verify e2e before flipping switches"
    is in MEMORY.md — this is the kind of gate he can't trust).

### Gap 5 — `turn_pipeline.VoiceProducer.produce()` stub is canonical under `ABVoiceProducer` fallback

- **Severity:** medium.
- **Biomimicry:** `honest` intent, `procedural` realization.
- **Evidence:** `turn_pipeline.py:161–214` defines `VoiceProducer.produce`
  as a *stub*. `ABVoiceProducer` (line 217) wraps it with voice_ab
  comparison, but falls back to the stub on framework-init failure or
  framework.produce exception. So the "stub" is the production voice
  every time the A/B path fails — and the stub produces things like
  `"Still working on this one."` when a blob has no action and no
  hypothesis (line 214). That's Igor's actual voice on every
  pipeline-resolve where A/B fails.
- **Proposed ticket:**
  - id: `T-voice-stub-fallback-audit`
  - title: Measure + fix VoiceProducer stub fallback rate
  - size: M
  - tags: [cognition, voice, turn-pipeline]
  - description:
    ABVoiceProducer silently falls back to the stub on any voice_ab
    exception. First: add a forensic_logger counter per fallback,
    and a TWM marker so NE sees it. Second: replace the stub's
    `"Still working on this one."` with a blob-aware fallback that
    at least surfaces the hypothesis or cites the cascade level.
    Third: if stub-fallback rate exceeds 20% over a day, a
    watchdog habit should fire a gap. Scope NOT included: the
    A/B framework itself, graduation logic, or the graph voice
    actor's generation quality. Files touched: `turn_pipeline.py`
    (VoiceProducer.produce, ABVoiceProducer.produce),
    `forensic_logger.py` (new counter).
  - **Disposal:** SHIP. The observability half is cheap and the
    lurking bug (Igor saying "Still working on this one." as his
    actual reply) is exactly the kind of reply Akien notices.

### Gap 6 — NE runs `_memory_auditor_pass` every cycle but it's gated on env flag

- **Severity:** low.
- **Biomimicry:** `honest`.
- **Evidence:** `narrative_engine.py:705–712`: memory-auditor pass is
  inside `run()`, gated `IGOR_MEMORY_AUDITOR_ENABLED`. This is fine,
  but the flag-check pattern is now the dominant pattern in NE:
  `IGOR_NE_LLM_ENABLED` (line 635), `IGOR_PREDICTION_ERROR_ENABLED`
  (595), `IGOR_NODE_ADOPTION_ENABLED` (2260), `IGOR_MEMORY_AUDITOR_ENABLED`
  (705), `IGOR_CONSOLIDATION_IDLE_MIN` (2117). NE is becoming a
  distribution of optional subsystems, each with its own env flag,
  each defaulting off. The docstring still describes these as
  first-class capabilities of NE.
- **Proposed ticket:**
  - id: `T-ne-feature-flag-consolidation`
  - title: Collapse NE's env-flag constellation into a single config
  - size: S
  - tags: [cognition, ne, config, hygiene]
  - description:
    Replace the 5 standalone `IGOR_NE_*_ENABLED` flags with a single
    `IGOR_NE_FEATURES` comma-separated list (`llm,prediction_error,
    node_adoption,memory_auditor,consolidation`) plus per-feature
    tuning kept as now. Make the default set explicit in one place
    (the docstring). Scope NOT included: changing the behavior of
    any single pass, or changing the NE trigger logic. Files
    touched: `narrative_engine.py`. Cross-cuts none.
  - **Disposal:** DEFER. Low-priority hygiene; SHIP when another NE
    touch happens.

### Gap 7 — `reasoners/base.py` module docstring still describes a 2-level hierarchy that never finished

- **Severity:** medium (doc clarity on HIGH-inertia file).
- **Biomimicry:** `n/a`.
- **Evidence:** `reasoners/base.py:33–56`: docstring describes
  "Level 1 — Transport base classes" and "Level 2 — Model family
  failover" with `ClaudeFamily` as an example. Level 2 has no live
  users (see Gap 2). The docstring is load-bearing per
  T-docs-live-in-code — and it claims a structural design that's
  absent.
- **Proposed ticket:**
  - id: `T-base-py-docstring-truth`
  - title: Rewrite `reasoners/base.py` docstring to match what's live
  - size: S
  - tags: [docs, live-in-code, reasoners, HIGH-inertia]
  - description:
    Promote the top-of-file docstring to the current live shape: no
    ClaudeFamily, no ModelFamily, no BrowserReasoner (assuming Gap 2
    closes), no D026 two-level hierarchy. What IS there: BaseReasoner
    ABC + token-economy shared utilities + _winnow_context bound
    method + LocalReasoner/APIReasoner thin tags. Keep the full
    TOKEN ECONOMY, CONTEXT ASSEMBLY, WINNOWING sections — those
    are canonical. **HIGH-inertia:** YES. Scope NOT included:
    BaseReasoner's reason() contract, or any behavior change.
    Files touched: `reasoners/base.py` (docstring only).
  - **Disposal:** INVESTIGATE. Pair with Gap 2 (delete-then-doc
    or doc-then-delete? doc-then-delete is safer).

### Gap 8 — NE sleep consolidation's "Hebbian" claim is procedural clustering

- **Severity:** high for biomimicry honesty.
- **Biomimicry:** `theatrical`.
- **Evidence:** `narrative_engine.py` docstring line 28 + 44 + 104
  explicitly claims the sleep pass is a "Hebbian wandering" (D353).
  Actual implementation: `_deep_consolidation_pass` at line 2134
  does (1) promote TWM obs at 0.5 salience threshold, (2) merge
  episodic clusters (cosine ≥ 0.80), (3) prune weak links, (4)
  adopt orphans, (5) integrate reading. None of these are Hebbian.
  The actually-Hebbian piece (arousal-weighted word-graph edge
  reinforcement) lives in `hebbian_bridge.py` and is flag-gated
  off (Gap 3). The sleep pass is k-means + link pruning with a
  sleep label.
- **Honest version:** During idle, replay recent `tails` + search
  traces; for each replayed pair of memories that were activated
  near each other in time (a "firing together" window), increment
  the interpretive edge weight between them. This is the mechanism
  the docstring claims. `replay.py` is probably where this
  belongs (sibling file) — but consolidation.py is currently the
  labeled home and it's doing something else.
- **Proposed ticket:**
  - id: `T-sleep-consolidation-honesty`
  - title: Honest Hebbian sleep pass OR retract the claim
  - size: L
  - tags: [biomimicry, ne, hebbian, honesty]
  - description:
    Two paths, choose one: (A) Implement a true replay-based
    Hebbian pass during idle: read recent search traces; for each
    within-turn node pair, bump the interpretive edge weight;
    strengthen the word-graph edges over the pair's shared
    vocabulary (arousal-scaled). This is the mechanism `D353` and
    the docstring claim. (B) Retract the Hebbian claim from NE
    docstring, rename `_deep_consolidation_pass` to what it
    actually does (`_idle_housekeeping_pass`), and move any
    Hebbian mechanism back into `hebbian_bridge.py` or a new
    module with an explicit gate. Either choice fixes the
    theatricality. Scope NOT included: changing what idle
    promotion/merge/prune actually do (those are honest on their
    own); changing `replay.py`. Files touched:
    `narrative_engine.py`, possibly `replay.py`.
  - **Disposal:** INVESTIGATE. This is a thesis-level biomimicry
    decision and belongs in a Pass 3 synthesis alongside area-2's
    Hebbian finding and area-5's consolidation finding.

### Gap 9 — `system_prompt.py` caches by role, but role isn't part of prompt_role threading

- **Severity:** low.
- **Biomimicry:** `n/a`.
- **Evidence:** `system_prompt.py:74` builds a cache key from
  `role + instance_id + |`-joined narratives. Fine. But
  `reasoners/base.py`'s docstring (line 128–134) says `prompt_role`
  is an optional per-call override gated on cloud reasoners. So
  the per-call override runs through the same cache — meaning a
  call with `prompt_role="analysis"` that lands on a cloud reasoner
  constructs the prompt fresh with role="analysis", caches it,
  and subsequent interactive calls with role="interactive" hit
  a different key (fine). But if two callers simultaneously call
  with the same role and instance_id, they'll race on `_cache`
  with no lock. Low probability (single-threaded main), but
  worth noting.
- **Proposed ticket:**
  - id: `T-system-prompt-cache-lock`
  - title: Protect `system_prompt._cache` with a lock
  - size: S
  - tags: [infra, prompt, hygiene, threading]
  - description:
    `_cache: dict` is mutated by `build_system_prompt` without a
    lock. Under the worker-pool pattern (when that lands), this is
    a race. Add a `threading.Lock()` around read+write. Scope NOT
    included: cache eviction, cache key shape. Files touched:
    `system_prompt.py`.
  - **Disposal:** DEFER. Only matters once workers are multi-thread
    for turns. Not urgent today.

### Gap 10 — `voice_ab`'s flatness scoring is a scalar proxy, not a content quality check

- **Severity:** medium.
- **Biomimicry:** `procedural-with-bio-name`.
- **Evidence:** `voice_ab.py:132–146`: GraphVoiceActor's score is
  `1.0 - flatness` where flatness is `max(0.0, 1.0 -
  min(max_w/1.0, 1.0))` — the higher the top-prediction weight,
  the less flat, the higher the score. That rewards predictable
  word-graph output. Problem: a word graph with one dominant edge
  ("the" → "the" → "the") would score 1.0. LLMVoiceActor (not
  shown but elsewhere in the file) has no similar scalar; its
  score is assumed reasonable. The "A/B" comparison is scalar-vs-
  scalar with different semantics — it's not comparing the same
  quality dimension.
- **Proposed ticket:**
  - id: `T-voice-ab-score-parity`
  - title: Put voice_ab scores on a common dimension
  - size: M
  - tags: [voice, ab, cognition, biomimicry]
  - description:
    Make both GraphVoiceActor and LLMVoiceActor score along the
    same axes — e.g. (coherence ≥ keyword match with blob
    hypothesis), (length within expected range), (novelty ≥ not a
    repeat of last reply). Combine into a final score the same
    way for both. Scope NOT included: the A/B framework contract,
    training signal into word graph, ABVoiceProducer fallback
    semantic (Gap 5). Files touched: `voice_ab.py` (scoring
    functions only).
  - **Disposal:** DEFER. Interesting biomimicry work but A/B is
    new; better to let usage data accumulate first. Pair with
    Gap 5.

---

## Dead-code cross-check

- **Habits referencing non-existent code in my area:** none found.
  The four habits documented in inference_gateway and
  narrative_engine docstrings — `PROC_SET_CLOUD_NOW`, `PROC_NIGHT_READ`,
  `PROC_NE_TRIGGER`, `PROC_SLEEP_CONSOLIDATION` — are referenced from
  `inference_gateway.py`, `narrative_engine.py`, `cloud_mode.py`, and
  a seed script. Did not audit the live habit DB to confirm each
  engram actually exists; flagging `INVESTIGATE` for Pass 3.
- **Code in my area not referenced by any habit or test:**
  - `BrowserReasoner` (`reasoners/base.py:840`) — unused (Gap 2).
  - `ModelFamily`, `ClaudeFamily` (`reasoners/base.py:865, 901`) —
    unused (Gap 2).
  - `_try_restart_local_ollama` (`inference_gateway.py:1300`) — one
    caller (`is_local_inference_available`), which is called by
    the gateway health check. Not dead, but very nearly so — the
    only caller is reached via a specific failure path.
  - `_t5` slot and its `None` assignment at `from_env` — tier.5 is
    inhibited. Code slot is dead.

---

## Summary

- Ticket candidates total: **18**
  (9 from Pass 1 findings + 9 from Pass 1 gaps + 1 thesis-crux
  escalation already in P9-a)

  Wait — re-counting against the rendered blocks: 9 Pass-1-finding
  tickets (P1-1, P1-2, P2-ev, P4-1, P5-a, P7-a, P8-a, P9-a) = 8,
  plus 9 Gap tickets (T-word-graph-docstring-drift,
  T-reasoner-hierarchy-prune, T-hebbian-bridge-enable-audit,
  T-cloud-ok-unify-semantic, T-voice-stub-fallback-audit,
  T-ne-feature-flag-consolidation, T-base-py-docstring-truth,
  T-sleep-consolidation-honesty, T-system-prompt-cache-lock,
  T-voice-ab-score-parity) = 10. Total **18**.

- **SHIP: 4**
  - T-reasoning-cache-sweep — disk-sweep, small, immediate win
  - T-word-graph-docstring-drift — one-file doc fix, respects rules
  - T-cloud-ok-unify-semantic — small, fixes live semantic drift
  - T-voice-stub-fallback-audit — the observability half is cheap;
    silent "Still working on this one." is high-annoyance bug

- **DEFER: 7**
  - T-main-loop-event-drive — runtime-measure first
  - T-twm-as-bus-enforcement — area-2 must bless TWM API first
  - T-retire-legacy-reasoner-path — needs metric in place
  - T-reasoner-hierarchy-prune — HIGH-inertia, waits for explicit go
  - T-ne-feature-flag-consolidation — hygiene, ride a future touch
  - T-system-prompt-cache-lock — only matters under multi-thread workers
  - T-voice-ab-score-parity — let A/B usage data accumulate

- **INVESTIGATE: 6**
  - T-process-inner-dismantle — XL, needs selector-loop design doc
  - T-twm-rehearsal-priming — biomimetically valid; short design doc first
  - T-tier-gate-integrity — Akien must bless the shape
  - T-gateway-feedback-loops — thesis-critical; L+, needs design doc
  - T-hebbian-bridge-enable-audit — thesis claim; decision needed
  - T-base-py-docstring-truth — HIGH-inertia, pair with prune
  - T-sleep-consolidation-honesty — thesis-crux; decision + design

- **DISCARD: 0**. None of the findings in this area are wrong enough
  to throw out. P1-2 (busy-wait) is the weakest; even it is a real
  smell worth runtime-profiling.

- **Highest-stakes single finding in this area:**
  **Gap 8 — NE sleep consolidation's "Hebbian" claim is theatrical.**
  The docstring-vs-code gap on the most-named biological mechanism
  (Hebbian co-activation, sleep consolidation, D353) is the single
  largest honesty hole in cognition. Every other finding is either a
  contained engineering issue or a real mechanism that's flag-gated
  off. This one is code that claims to be Hebbian while doing
  cosine-clustering-with-pruning.

- **One sentence for Pass 3:**
  Decide whether Igor's thesis commits to Hebbian co-activation as a
  live mechanism (ship the bridge + real replay-based sleep pass) or
  retracts the claim from docstrings (NE, reasoners/base, word_graph,
  hebbian_bridge), because the current middle state — code present,
  flag off, docstrings confident — is the largest biomimetic-honesty
  hole in cognition + reasoning.
