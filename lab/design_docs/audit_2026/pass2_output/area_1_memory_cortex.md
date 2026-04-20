# Pass 2 deep-dive — Memory + Cortex

Auditor: Claude Opus 4.7 (1M context), Pass 2
Target area: `wild_igor/igor/memory/` — cortex.py, models.py, reconsolidation.py,
episode_binder.py, plus the ring_memory + twm_observations + memory_blobs +
interpretive_edges + tails + traces subsystems.

---

## Per-finding verdicts

### Finding P2-F1 — Pervasive filesystem/DB duality (Pass 1 persona 2)

- Verdict: CONFIRMED_NARROWER for this area. Cortex itself is Postgres-only —
  no filesystem shadow of `memories`, `twm_observations`, `ring_memory`,
  `memory_blobs`, `interpretive_edges`, `tails`, or `traces`. The duality
  Pass 1 flagged (decisions_log.dsb, queue.json, palace echoes) lives
  outside memory/. Within cortex, the one disk artifact is the embedding
  cache at `~/.TheIgors/cache/embeddings/`, which is a legitimate cache
  (regenerable from DB), not a second source of truth.
- Blast radius: n/a for memory. Handoff to area 8 (infra + db + tests).
- Biomimicry: n/a.
- Proposed ticket: none from this area. Referring to area 8.

### Finding P2-F2 — memory_blobs overlaps with `payload` column (Pass 1 persona 3)

- Verdict: REFUTED. The DB engineer conflated two distinct concerns.
  - `memory_blobs.content` holds large textual content for REFERENCE
    memories (design docs, distilled CSB, source code chunks). The
    narrative column intentionally stays short-and-searchable; the blob
    is fetched on demand via `get_blob(memory_id)` and spliced at
    relevance >= 0.5 by `expand_blob_memories()` (cortex.py:1941).
  - `memories.payload` (D260) holds engram program cells + data fields —
    structured JSON, not free text. `payload.NARRATIVE` is an
    embedding-source override (models.py:120). Executor touches only
    cell fields.
  - These have different read paths, different index discipline (no
    index on `memory_blobs.content`; GIN tsvector m034 on payload), and
    different gates. Merging them would muddle retrieval.
- Blast radius: n/a (refuted).
- Biomimicry: n/a.
- Proposed ticket: none.

### Finding P2-F3 — "Engram" is a single row, not an ensemble (Pass 1 persona 5 + 6)

- Verdict: CONFIRMED. A `Memory` (models.py:73) is one row. `payload.cells`
  (D260) is structured program not sparse distributed coactivation. The
  central term "engram" is semantically overloaded. The `Memory`
  dataclass is the unit of storage AND retrieval AND "engram" in
  docstrings. No ensemble id. No pattern completion from partial cue
  to ensemble. No sparse-distributed representation anywhere.
- Blast radius: EXTREMELY WIDE. `Memory` is HIGH-inertia (models.py in
  CLAUDE.md's HIGH list, BASE_INERTIA 0.95 on CORE_PATTERN, touched by
  every store/search/recall in the codebase — approx. 300+ call sites).
  Changing the primary unit from "node" to "ensemble" is a refactor of
  the whole project. cortex.search, NE, habit dispatch, MCP
  `memory_get`, scope discipline, inertia formula, spreading activation
  all assume one-id→one-node.
- Biomimicry: theatrical. The honest version: introduce an `engram_id`
  column (nullable) linking co-encoded nodes. Retrieval by
  `engram_id` reactivates the whole ensemble; search returns the
  ensemble centroid, not an individual node; pattern completion
  becomes a first-class operation ("given node A and B, which
  ensemble wants to fire?"). Single-node memories continue to work
  (engram_id = node_id for ensemble-of-one). This is additive, not
  destructive — no existing row has to change.
- Proposed ticket:
  - id: T-engrams-as-ensembles
  - title: Engram-as-ensemble — introduce engram_id so co-encoded nodes fire together
  - size: XL
  - tags: [biomimicry, memory, engram, high-inertia, design-spike]
  - description: The central biological claim of TheIgors is that
    memory is engram-shaped — sparse distributed ensembles that
    co-activate. Today, `Memory` is a single node with a `payload`
    of program cells. That's cognitively procedural, not neural.
    Introduce an `engram_id` (TEXT, nullable, indexed) column on
    `memories`. Co-encoded nodes (same store() call cluster,
    episode_binder output, consolidation-derived pattern) share an
    engram_id. Add `cortex.recall_engram(engram_id)` that reactivates
    every member with summed activation. Pattern completion:
    `cortex.complete_engram(seed_ids)` returns the ensemble ids that
    best match a partial cue, using interpretive_edges to reconstruct
    the set. Search can optionally promote an engram as a unit: if
    3+ ensemble members rank in top-20, boost the whole ensemble to
    top. Do NOT change: the `Memory` dataclass (engram_id on metadata
    is acceptable for phase 1, promote to column after data shape
    stabilizes), existing retrieval paths (engram-awareness is
    opt-in), or the inertia formula initially. HIGH-inertia scope
    note: this touches `models.py`. Phase 1 is stash-in-metadata
    (no schema change), phase 2 is the column. Old non-engrammed
    memories stay — they're ensemble-of-one.
  - disposal: INVESTIGATE — this is the single highest-stakes finding
    in memory. Design spike first, not immediate ship. Run the spike
    against a real consolidation cycle and see whether the ensemble
    actually carries signal the single-node version misses. If yes,
    promote to L ticket; if no, DISCARD with a note.

### Finding P2-F4 — "Attractor" is a Top-K query, not a basin (Pass 1 persona 5)

- Verdict: CONFIRMED. Two separate misuses of the word.
  - `cortex.get_attractors()` (cortex.py:5235) is literally
    `ORDER BY activation_count * (1 + COUNT(inbound)) DESC LIMIT N`
    — a popularity ranking over the memory graph.
  - `twm_set_attractor`/`twm_get_attractor` (cortex.py:4298+) is
    mildly better — it's a slot-weight competition with decay — but
    it's still not a basin. Nothing "falls into" the attractor; it's
    just a high-weight flag that the NE reads.
- Blast radius: MEDIUM. `get_attractors` is called by `adopt_orphans`,
  MCP `hot_attractors`, tools/graph_ops.py, push_sources. `twm_set_
  attractor` is called by UserInputSource and other push_sources.
  Rename or semantic split is a naming refactor, not a structural
  one.
- Biomimicry: theatrical (attractors-as-popularity) + procedural-
  with-bio-name (attractor-as-slot-flag). The honest version of a
  dynamical-systems attractor: a state trajectory. Spreading
  activation run over multiple steps from a fixed seed SHOULD
  converge to a steady-state heat distribution — that's the basin.
  The basin's "id" is the high-heat node that most activations
  flow into over time. You don't `LIMIT N` from a table — you
  iterate the spreading_activation function until delta < epsilon
  and read the fixed-point.
- Proposed ticket:
  - id: T-attractor-semantics-split
  - title: Rename get_attractors to get_hot_nodes and implement true
    fixed-point attractors for spreading activation
  - size: M
  - tags: [biomimicry, memory, naming, spreading-activation]
  - description: "Attractor" has two live meanings in cortex, both
    procedural-with-bio-name. Split the word. (1) Rename
    `cortex.get_attractors()` → `cortex.get_hot_nodes()` (and the
    MCP tool). Update callers (graph_ops.py, push_sources.py,
    adopt_orphans, tests). This is a pure rename, no behavior
    change. (2) Keep `twm_get_attractor`/`twm_set_attractor` as-is
    (the slot-competition is a legitimate GWT mechanism) but rename
    internally to `twm_set_focus` / `twm_get_focus` to stop overloading
    "attractor". (3) NEW: implement `cortex.fixed_point_attractors(seed_ids, max_iters=20, eps=0.01)`
    — iterate spreading_activation from seeds until convergence;
    return the high-heat nodes as the basin members. This becomes
    the TRUE attractor API — Igor can ask "given this TWM state,
    what attractor basin am I in?" Do NOT change: existing
    spreading_activation semantics, database schema, interpretive_edge
    semantics. Scope: memory/cortex.py + all `get_attractors` callers
    + MCP surface. Safe to delete old names after 1 session.
  - disposal: SHIP (the rename half); DEFER the fixed_point_attractors
    half to after T-engrams-as-ensembles lands — don't pile
    biomimicry changes on each other.

### Finding P2-F5 — Hebbian co-activation is counting, not spike-timing (Pass 1 persona 5)

- Verdict: CONFIRMED_NARROWER. `_apply_trail_training` (cortex.py:2796)
  IS closer to real STDP than Pass 1 gave credit for — it has LTP/LTD
  multipliers keyed on sequence position (i<j → LTP, else LTD), a
  learning rate, a creation threshold, and bounds. This is a
  reasonable Hebbian implementation. `hebbian_bridge.py` is also
  legitimate within its domain (word graph reinforcement). What IS
  misleading is that `_apply_trail_training` is gated by default,
  and its "co_activation" edges coexist in `interpretive_edges` with
  semantic meaning edges of direction='activation'|'inhibition'. The
  sloppiness is in the schema, not the math.
- Blast radius: NARROW. The trail training is gated by
  `IGOR_TRAIL_TRAINING_ENABLED` (currently ON in .env per D358). It
  only runs inside search(). One table (`interpretive_edges`) carries
  both semantic and learned edges.
- Biomimicry: honest (the STDP math) + procedural-with-bio-name (the
  name-collision with semantic interpretive edges). Honest version:
  split co_activation edges into their own table or add a
  `layer='trail_training'` filter everywhere edges are read
  (already done partially — cortex.py:2887 layers the edge; most
  readers don't filter).
- Proposed ticket:
  - id: T-co-activation-edge-separation
  - title: Separate Hebbian co_activation edges from semantic interpretive edges
  - size: S
  - tags: [memory, schema, biomimicry-hygiene]
  - description: `_apply_trail_training` writes co_activation edges
    into `interpretive_edges` alongside semantic
    activation/inhibition edges. Readers like
    `get_interpretive_edges`, `interpretive_traverse`, and
    `get_meaning_to_me` don't consistently filter — semantic
    readers can pick up Hebbian edges and treat them as meaning.
    Fix by (a) filtering every read path by `layer !=
    'trail_training'` when the reader is semantic, OR (b) moving
    co_activation edges to a `co_activation_edges` table with the
    same shape. Prefer (a) — cheaper, reversible. Audit every
    `SELECT FROM interpretive_edges` and decide per caller whether
    trail-training edges belong. Do NOT change: the trail training
    math, the edge schema for semantic edges, or any habit that
    reads edges. Safe to ship on its own.
  - disposal: SHIP. Low risk, high clarity. Affects correctness of
    semantic retrieval once enough co_activation edges accumulate.

### Finding P2-F6 — TWM is a list with a ceiling, not working memory (Pass 1 persona 7)

- Verdict: CONFIRMED_NARROWER. Pass 1 missed a critical distinction:
  - TWM_MAX=50 is the raw OBSERVATION buffer cap — a ring-buffer
    rate-limiter, analogous to sensory buffer capacity.
  - TWM_MAX_SLOTS=7 is the ATTRACTOR slot cap — a true 7±2 GWT
    workspace (D099). The attractor API (`twm_set_attractor`,
    `twm_get_slots`, `twm_decay_slot`) IS Baars-style with
    competition: setting a new attractor at capacity evicts the
    weakest (cortex.py:4317-4321). Solo slots decay at 0.7 via NE's
    comparison pass.
  - What's missing is ACTIVE maintenance / rehearsal. Items decay
    by TTL or slot-decay; there's no positive "rehearse this"
    operation that resurrects an expiring TWM item because it's
    still relevant. `twm_extend_ttl` (cortex.py:4517) comes close
    but is triggered only by Signal C (relevance >= 0.6 search
    hit) — it's passive recognition, not active rehearsal.
  - Also missing: rehearsal loop coupled to active goal. Igor should
    re-ping high-salience TWM items whose topic is the active goal.
- Blast radius: MEDIUM. Changes to TWM push/evict touch every push
  source (20+ files) and NE's integration loop.
- Biomimicry: honest (slot competition) + missing-mechanism (no
  rehearsal). Honest version: add a rehearsal heartbeat.
- Proposed ticket:
  - id: T-twm-rehearsal-loop
  - title: TWM rehearsal — goal-coupled re-ping for active attractor slots
  - size: M
  - tags: [twm, biomimicry, working-memory]
  - description: TWM has slot competition and TTL but no active
    rehearsal. In biological WM, items stay alive via attentional
    refocus (dorsolateral PFC re-pinging). Today, a TWM item that
    matters to the current goal decays on TTL like any other.
    Implement `twm_rehearse(obs_id)` that extends TTL AND increments
    integration_count (showing the slot was re-focused). Add a
    heartbeat in NE that looks at the active goal and re-rehearses
    any TWM item whose content overlaps ≥2 tokens with the goal
    text, every 60s. Cap: rehearse max 3 slots per heartbeat. Do
    NOT change: push semantics, attractor competition, TTL default,
    or urgency gate. This is pure additive biomimicry — Igor goes
    from "sensory-driven TWM fade" to "goal-driven TWM rehearsal".
  - disposal: DEFER — needs an honest measurement first. Build a
    traceable telemetry (how often does a TWM item the user clearly
    cares about silently decay before being used?) and only ship
    if the signal shows the gap is real.

### Finding P2-F7 — Spreading activation exists but is disconnected from priming (Pass 1 persona 7)

- Verdict: CONFIRMED. `cortex.spreading_activation()` is called by NE
  (for prediction-error training and coalition detection, lines 603 +
  677 of narrative_engine.py) but its output (the heat_field) never
  primes subsequent cortex.search() candidate scores. Priming in the
  cognitive-science sense (doctor→nurse) is absent. The `_spread_
  activation` private method is graph-neighbor boosting AFTER search
  — not before, so it's extension, not priming.
- Blast radius: MEDIUM. Wiring heat_field into search() adds one
  optional parameter; the primed scores reshape candidate ranking.
  Touches cortex.search signature (back-compat needed) and NE
  (pass the heat forward).
- Biomimicry: procedural-with-bio-name. Mechanism exists, wiring
  missing. Honest version: NE runs spreading_activation every turn
  from TWM top-7; stashes the result on the cortex instance as
  `_current_heat_field`; cortex.search adds heat_field scores to
  candidate relevance BEFORE Phase 2 rerank. Heat decays with TTL
  (60s, matches NE cycle).
- Proposed ticket:
  - id: T-priming-via-spreading-activation
  - title: Wire spreading_activation heat_field into cortex.search priming
  - size: M
  - tags: [biomimicry, cortex, spreading-activation, cognition]
  - description: spreading_activation() produces a heat_field dict
    that currently feeds only coalition detection + prediction-error
    training. True priming requires that heat inform retrieval. Add
    a `_current_heat_field: dict[str, float]` attribute on Cortex,
    cleared on timeout (60s). NE populates it from its TWM-seeded
    spreading_activation call. cortex.search checks `_current_heat_
    field`; candidates with heat > 0 get a proportional relevance
    bump (clamped 0.10 max). Priming is additive to existing scoring;
    if NE hasn't populated it, search is unchanged. Do NOT change:
    NE's coalition detection, the TWM push surface, or existing
    phase 2 rerank behavior. Delete-safety: back out by removing the
    attribute + bump logic; no persistent state.
  - disposal: SHIP. This is the cheapest biomimicry win in the area
    — existing mechanisms just aren't wired together.

### Finding P2-F8 — Memory reconsolidation is half-wired (Pass 1 persona 5 + 6)

- Verdict: CONFIRMED_WORSE. Pass 1 called this "honest" but missed
  that there are TWO PARALLEL reconsolidation mechanisms that don't
  talk to each other:
  - Path A: `_flag_for_reconsolidation` (cortex.py:2602) sets
    `metadata.reconsolidate_pending` on high-importance retrievals
    under arousal ≥ 0.4. Consumed by `NE._reconsolidation_pass`
    (narrative_engine.py:1543). This path is LIVE and wired.
  - Path B: `reconsolidation.py` module with `mark_recalled`,
    `confirm_recall`, `contradict_recall`. Writes
    `metadata.reconsolidation_flag` (different key!). Consumed by:
    nobody. Tests only (tests/test_reconsolidation.py). The module
    docstring (reconsolidation.py:42-48) explicitly lists the
    downstream wiring as future work.
  - `hook_search_results` IS called by cortex.search (line 2561)
    so memories DO get marked as recall-pending. But nothing ever
    calls `confirm_recall` or `contradict_recall`, so the tracker
    just accumulates until `clear_pending` runs in a test. Memory
    leak under long runs: `_recall_pending` dict grows unbounded
    until Igor restarts.
- Blast radius: HIGH. Two parallel flag keys (`reconsolidate_pending`,
  `reconsolidation_flag`) is technical debt. The `_recall_pending`
  dict is a slow memory leak — not observable in test runs but
  real over a 72-hour session.
- Biomimicry: Path A honest (arousal-gated, context-hashed, wired
  to NE rewrite); Path B procedural-with-bio-name (the "lability
  tracker" is just a dict with no consumers).
- Proposed ticket:
  - id: T-reconsolidation-unification
  - title: Unify reconsolidation paths — wire contradict_recall or delete it
  - size: M
  - tags: [memory, biomimicry, dead-code, reconsolidation]
  - description: Cortex has two reconsolidation mechanisms with
    different flag keys and zero crosstalk. Decide which is
    canonical. Recommend Path A (arousal-gated, NE-consuming)
    stays as the mechanism; Path B's consumer-side functions
    (`confirm_recall`, `contradict_recall`) either get wired to
    real downstream signals (action_claim_verifier misfires,
    response_coherence_inhibitor flags) or get removed. If
    wiring is the path, `contradict_recall` should write to the
    SAME metadata key as Path A so `NE._reconsolidation_pass`
    picks it up. If deleting is the path, remove
    `reconsolidation.py`'s consumer functions AND
    `hook_search_results` — keeping the hook without consumers
    is a silent memory leak (the `_recall_pending` dict grows
    unbounded). Do NOT change: NE's pass, `_flag_for_reconsolidation`,
    or the `reconsolidate_pending` metadata key.
  - disposal: SHIP. Leaving two half-wired paths is actively
    confusing and leaks memory. Even the "delete Path B" option
    is strictly better than status quo.

### Finding P2-F9 — Silent engrams absent (Pass 1 persona 6)

- Verdict: CONFIRMED. No distinction between "encoded but sub-
  threshold" and "never encoded". `cortex.search` returning empty
  is treated as absence.
- Blast radius: LOW for the detection side (add a `retrievability`
  float). Wide for the search side if retrievability gates are
  introduced.
- Biomimicry: missing-mechanism.
- Proposed ticket:
  - id: T-silent-engrams-retrievability
  - title: Add retrievability float to distinguish silent from absent memories
  - size: M
  - tags: [biomimicry, memory, engram]
  - description: Biologically, an engram can be encoded but below
    retrieval threshold under normal cues; a specific cue (the
    computational analog of optogenetic reactivation) recovers it.
    Today, `cortex.search` returning empty is ambiguous — was the
    memory never encoded, or encoded but not surfaceable? Add
    `retrievability: float = 1.0` on `Memory` (HIGH-inertia —
    touches models.py; phase 1 can stash it in metadata).
    `cortex.search` only considers candidates with retrievability
    ≥ threshold (default 0.05 — silent, but not zero). A new
    `cortex.search_silent(query, cue_strength=high)` lowers the
    threshold to surface silent engrams. Decay path: low activation
    + high age reduces retrievability over time, approaching but
    never reaching zero (memories don't get deleted, they go silent).
    Do NOT change: inertia formula (separate concept — inertia is
    edit-resistance, retrievability is surfaceability), existing
    search calls (retrievability defaults to 1.0 on all current
    rows). HIGH-inertia flag: touches `models.py`.
  - disposal: INVESTIGATE. This is the mechanism Akien's
    "CP6 — no cached trust, re-test priors" epistemology actually
    demands. But the cost of wiring it everywhere vs. the payoff
    needs a spike. Run against the corpus first.

### Finding P2-F10 — Interference and forgetting absent (Pass 1 persona 6)

- Verdict: CONFIRMED. No lateral inhibition between similar memories
  at recall time. `cortex.search` returns a ranked list; retrieved
  nodes don't suppress similar-but-not-retrieved neighbors. Forgetting
  is activation-count decay only — no pruning, no archival.
- Blast radius: MEDIUM. Adding lateral inhibition to search changes
  top-k ranking.
- Biomimicry: missing-mechanism.
- Proposed ticket:
  - id: T-lateral-inhibition-at-recall
  - title: Retrieval-induced forgetting — lateral inhibition among near-siblings
  - size: M
  - tags: [biomimicry, memory, cortex, forgetting]
  - description: Biological retrieval suppresses competing memories
    (retrieval-induced forgetting, Anderson 1994). Today, cortex.search
    produces a ranked list with no retrieval-time competition.
    Implement: after top-k selection, for each winner, scan the top-30
    candidates for similar-narrative siblings (cosine > 0.7 on
    embedding); apply a 10% temporary activation penalty (TTL 5 min,
    in-memory, not persisted). Losers this turn stay lower on the
    next turn too. Combined with existing decay this approximates
    "useful memories get more findable, near-misses fade". Do NOT
    change: activation_count (never penalize the stored value),
    stored narratives, or interpretive_edges. Scope: cortex.search
    only. Revertible by removing the inhibition step.
  - disposal: DEFER. Real biomimicry but costs cosine pairwise ops
    per search. Measure search latency first (P99 likely already
    >200ms). Only pursue if T-engrams-as-ensembles lands — then
    the inhibition is between ensembles, which is both cheaper and
    more biologically correct.

### Finding P2-F11 — Place/context coding stored, never used for retrieval (Pass 1 persona 6)

- Verdict: CONFIRMED. `context_of_encoding` is set on store (9+ call
  sites across seed scripts, reasoners, reading_indexer, main.py,
  NE, pr_accretion) and returned on read (cortex.py:3838), but
  `cortex.search` never filters or scores by it. The field is
  documentation/provenance, not retrieval signal.
- Blast radius: NARROW. Adding a `context_filter` optional parameter
  to cortex.search is a back-compat addition.
- Biomimicry: procedural-with-bio-name (hippocampal context
  coding exists as a field, not as a retrieval mechanism).
- Proposed ticket:
  - id: T-context-dependent-recall
  - title: Use context_of_encoding as a soft retrieval signal
  - size: S
  - tags: [biomimicry, cortex, hippocampal-analog]
  - description: Every memory stores `context_of_encoding`
    (free-text tag of "what was happening"). No retrieval path
    uses it. Add optional `context: str` parameter to cortex.search
    that, when provided, gives a small relevance boost (+0.05) to
    candidates whose `context_of_encoding` shares ≥2 tokens with
    the current context. Callers pass the current NE/milieu
    context string. Do NOT change: default behavior (unset →
    current ranking unchanged), the context_of_encoding column,
    or any writer. Scope: cortex.search signature + one scoring
    function. Safe to ship.
  - disposal: SHIP. Cheapest honest biomimicry win in the area.

### Finding P2-F12 — TWM salience runaway feedback loop (Pass 1 persona 9)

- Verdict: CONFIRMED_NARROWER. The G6 habituation (cortex.py:4075-4097)
  halves salience on repeats (0.5^repeats, floor 0.05) and G47 rejects
  repeats above 4 outright (cortex.py:4102-4106). So the runaway is
  bounded — what's NOT bounded is the TIME window for habituation.
  The existing check looks at `integrated = 0` twm_observations with
  same 120-char signature, so once something integrates (or expires)
  it habituates fresh again. A topic can keep re-entering as "novel"
  every cycle.
- Blast radius: LOW. Widening the habituation window is a one-line
  change.
- Biomimicry: honest (habituation mechanism) + narrow-scope (window
  too short).
- Proposed ticket:
  - id: T-twm-habituation-window-widen
  - title: Extend TWM habituation to cross integration/expiry boundaries
  - size: S
  - tags: [twm, habituation, biomimicry]
  - description: G6/G47 habituate on TWM push only when the same
    content signature is present in a CURRENT
    `integrated=0` observation. Once the observation integrates,
    the signature resets — allowing the same topic to re-enter
    as "novel" every NE cycle. Extend the signature check to
    include the last N hours of all observations (integrated or
    not, expired or not), stored as a rolling bloom filter or a
    small signature_history table. Signature match within 2h
    triggers same habituation decay. Do NOT change: the habituation
    math, the floor, the urgency escape hatch, or G47's repeat
    threshold. Scope: twm_push signature lookup SQL.
  - disposal: DEFER. Needs a measurement first — log how often
    the same signature re-enters TWM within 2h. If rare, no ship;
    if common, ship.

### Finding P2-F13 — _mem_cache unbounded under long runs (Pass 1 persona 4)

- Verdict: CONFIRMED. `Cortex._mem_cache` (cortex.py:210-211, 3857-
  3872) has TTL (300s for non-genesis) but no size cap. Every unique
  memory ID accessed adds an entry; expired entries are removed only
  on subsequent get (lazy). Over a 72h session with thousands of
  unique memory touches, the dict grows. Not a crisis — entries are
  small — but it violates the "hardware-friendly" principle.
- Blast radius: NARROW. Adding a size cap + LRU eviction is
  localized to the cache helpers.
- Biomimicry: n/a (pure infrastructure).
- Proposed ticket:
  - id: T-mem-cache-lru-cap
  - title: Cap cortex._mem_cache with LRU eviction
  - size: S
  - tags: [memory, infra, small-hardware]
  - description: `_mem_cache` has TTL but no size limit. Under a
    72h run the dict grows monotonically (expired entries are
    popped only on access). Cap at MAX_CACHE_ENTRIES=2000 and
    evict LRU (`OrderedDict`/`functools.lru_cache` won't work
    directly because of the permanent-genesis rule — use an
    OrderedDict with manual move_to_end on get). Genesis types
    (ROOT/CORE_PATTERN/IDENTITY) pinned, not subject to LRU
    eviction. Do NOT change: cache TTL, cache invalidation
    semantics, or caller code. Scope: `_cache_put` / `_cache_get`
    / `_cache_fetch_ids` only.
  - disposal: SHIP. Small, safe, addresses a known small-hardware
    issue.

### Finding P2-F14 — get_by_type / scope scan warning vs D199 (Pass 1 persona 3 N+1)

- Verdict: NEEDS_RUNTIME. Several methods in cortex run SELECTs with
  `LIMIT N` but no activation filter (e.g., _get_context_anchors:3450-
  3454 pulls 200 narratives sequentially, reads them into memory,
  scores them, returns top 2). At small graph scale this is fine; at
  11k+ memories it's a row scan in the "no-row-scans" (D199, D221)
  architecture. Same pattern in a few other places.
- Blast radius: LOW-MEDIUM performance.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-cortex-row-scan-audit
  - title: Audit cortex for LIMIT-200 scans that violate D221 no-row-scans
  - size: S
  - tags: [cortex, performance, tech-debt]
  - description: Some methods still fetch a fixed-size slice and
    scan narratives in Python (e.g. `_get_context_anchors` pulls
    200 rows to find 2). Grep cortex.py for `LIMIT 100`/`LIMIT
    200`/`LIMIT 300` and audit each — does it have an index? Does
    it filter activation_count? Do the work in SQL (tsvector match
    or trigram, ordered by activation) rather than fetching-and-
    scoring-in-Python. Do NOT refactor retrieval semantics — just
    move scoring into SQL. Scope: cortex.py only.
  - disposal: INVESTIGATE. Depends on runtime measurement. If
    anchor lookup takes <10ms at current scale, DEFER. If >100ms,
    SHIP.

---

## Pass 1 gaps (findings Pass 1 missed in this area)

### Gap G1 — Docstring claims ring_memory is per-instance; schema doesn't support it

- Severity: medium
- Biomimicry: n/a
- Evidence: cortex.py:41-42 docstring says
  `Indexed by instance_id so each Igor box gets its own ring.
  Columns: id, content, timestamp, instance_id, thread_id.`
  But the actual CREATE TABLE (cortex.py:282-288) is:
  `ring_memory (id SERIAL, category TEXT, content TEXT,
  timestamp TEXT, thread_id TEXT)` — NO instance_id column.
  Cross-instance ring data would mix if Igor ever ran multi-instance
  against shared `ring_memory`. (Currently the ring lives in the
  local proxy, so in practice each box has its own, but the
  docstring promise is wrong.)
- Proposed ticket:
  - id: T-ring-memory-docstring-fix
  - title: Fix ring_memory docstring (no instance_id column) + add if needed
  - size: XS
  - tags: [docs, cortex, schema]
  - description: cortex.py docstring (line 41-42) promises
    `ring_memory` is instance-scoped by an `instance_id` column.
    The schema has no such column. The per-instance isolation
    actually comes from `make_local_proxy` pointing at a per-box
    DB. Either fix the docstring to say "instance scoping via
    local DB, not a column" OR add the column if cross-instance
    ring reads ever become needed. Recommend fix docstring —
    the local-DB scoping is fine and simpler.
  - disposal: SHIP. Docstring lies to readers; easy fix.

### Gap G2 — `context_of_encoding` not used in recall, but claimed as "context coding"

This is half-included in finding P2-F11 — but Pass 1 tagged it as a
retrieval gap only. The DEEPER gap: `context_of_encoding` is a single
free-text string, which is weak vs. hippocampal grid-like context codes.
A more biomimetically honest implementation would be a vector (place +
time + mood + task). That's out of scope for now but should be in the
"what's missing" list.

- Severity: low (design sketch)
- Biomimicry: procedural-with-bio-name
- Proposed ticket:
  - id: T-context-vector-upgrade
  - title: Upgrade context_of_encoding from string to vector for richer place-coding
  - size: L
  - tags: [biomimicry, memory, design-spike, deferred]
  - description: Deferred design note. Context-dependent recall
    works better when "context" is a structured vector (place,
    time, mood, active task, salient topic) rather than a free
    string. Out of scope until T-context-dependent-recall (P2-F11)
    ships and we see where the string version falls short.
  - disposal: DEFER. Do not ship until string version measured.

### Gap G3 — `reconsolidation._recall_pending` dict leak

Already rolled into P2-F8 — flagging again to make sure Pass 3 sees
this as a memory-leak concern, not just a design concern.

### Gap G4 — `_flag_for_reconsolidation` writes via store() inside search()

- Severity: medium
- Biomimicry: n/a (performance/correctness)
- Evidence: cortex.py:2657-2659 — every search that surfaces a
  high-importance memory under high arousal does a full
  `self.store(mem)` write, which writes ALL columns + triggers
  `_auto_wire_interpretive` + `_maybe_calve`. That's heavy for a
  metadata-flag-only update.
- Proposed ticket:
  - id: T-reconsolidation-flag-cheap-write
  - title: Flag-for-reconsolidation should do a metadata-only UPDATE, not full store()
  - size: S
  - tags: [cortex, performance, reconsolidation]
  - description: `_flag_for_reconsolidation` currently does
    `cortex.store(mem)` to persist flag metadata. `store()` runs
    scrub, provenance, test-data-lifecycle, versioning,
    auto-wire-interpretive, and calving checks. For a metadata-only
    flip, that's ~10 useless operations per flagged memory per
    search under arousal. Add a `_update_metadata_only(mem_id,
    metadata_patch)` internal method that does a single UPDATE.
    Do NOT change: flag semantics, NE's consumer, or when the
    flag is set.
  - disposal: SHIP after P2-F8 (reconsolidation unification)
    lands. Don't pile writes on the wrong path.

### Gap G5 — TWM `twm_read` ORDER BY id ASC suggests oldest-first, but NE expects most-salient-first

- Severity: low-medium
- Biomimicry: n/a
- Evidence: cortex.py:4203 `ORDER BY id ASC LIMIT ?` — NE readers
  that want top-salient have to sort in Python. Multiple callers
  do `sorted(twm_read(...), key=salience)`. If TWM ever exceeds
  50 entries (it can momentarily during a burst), high-salience
  items can be beyond the limit window.
- Proposed ticket:
  - id: T-twm-read-order-by-salience
  - title: twm_read should offer salience-ordered mode
  - size: XS
  - tags: [twm, cortex, api]
  - description: Add optional `order: str = "id_asc" | "salience_desc"
    | "urgency_desc"` parameter to `twm_read`. Default stays
    `id_asc` for back-compat. Callers that want top-salient
    (NE coalition detection, context anchor builder) pass
    `"salience_desc"`. Do NOT change: the default, the schema,
    or callers that already sort in Python (they can migrate
    opportunistically).
  - disposal: SHIP. Trivial and clarifies intent at call sites.

### Gap G6 — `get_attractors` (soon get_hot_nodes) excludes PROCEDURAL but not INTERPRETIVE

- Severity: low
- Biomimicry: n/a
- Evidence: cortex.py:5247 — `WHERE m.memory_type NOT IN
  ('PROCEDURAL')`. Habits are excluded but INTERPRETIVE edges/nodes
  aren't, so a heavily-used interpretation node shows up as an
  "attractor" equally with a factual topic. That's probably fine for
  introspection but semantically mixes two kinds of hot nodes.
- Proposed ticket:
  - id: T-hot-nodes-typed
  - title: get_hot_nodes should return typed views (knowledge vs interpretation vs habit)
  - size: S
  - tags: [cortex, api, mcp]
  - description: `get_attractors` (after rename → get_hot_nodes)
    mixes FACTUAL, INTERPRETIVE, EPISODIC, and everything-except-
    PROCEDURAL. Add `type_filter` parameter; return typed groups
    for MCP consumers (hot_knowledge, hot_interpretations, hot_
    episodes). Do NOT change: the scoring function, the default
    behavior, or procedural exclusion.
  - disposal: DEFER. Not load-bearing.

### Gap G7 — episode_binder.replay_episodes uses cortex.search("episode_binder") which is a keyword hack

- Severity: medium
- Biomimicry: procedural-with-bio-name
- Evidence: episode_binder.py:313-317 — to find episodes, it calls
  `cortex.search("episode_binder", memory_types=["EPISODIC"])`. This
  depends on the literal string "episode_binder" being in the
  narrative or metadata, which is pattern-fragile. A more honest
  retrieval would be `SELECT WHERE metadata->>'deposited_by' =
  'episode_binder'`.
- Proposed ticket:
  - id: T-episode-binder-replay-direct-query
  - title: replay_episodes should query by metadata.deposited_by, not keyword search
  - size: S
  - tags: [episode-binder, memory, tech-debt]
  - description: `replay_episodes` uses a free-text search for
    the literal "episode_binder" to find deposited episodes. That's
    fragile (any memory mentioning the word would match) and
    wasteful (runs full search pipeline for a simple metadata
    lookup). Replace with a direct DB query filtering by
    `metadata->>'deposited_by' = 'episode_binder'` and the
    timestamp_start window. Same for `complete_episode`. Do NOT
    change: the Episode dataclass, the deposit path, or the
    downstream consolidation consumers.
  - disposal: SHIP. Small, cheap, correctness win.

### Gap G8 — No explicit separation between class/instance scope in twm_read filter logic

- Severity: low
- Biomimicry: n/a
- Evidence: cortex.py:4179-4195 — twm_read filters by `instance_id`
  only if `self._instance_id` is set. Other Cortex methods gate by
  scope explicitly. TWM is intrinsically instance-local by design,
  but the filter depends on the Cortex object being constructed
  with an instance_id. A Cortex with `instance_id=None` returns
  cross-instance TWM, which is surprising.
- Proposed ticket:
  - id: T-twm-instance-gate-default
  - title: twm_read should default to instance-scoped, require explicit cross-instance opt-in
  - size: XS
  - tags: [twm, cortex, safety]
  - description: `twm_read` silently returns cross-instance
    observations when `self._instance_id` is None. This is a
    subtle scope leak. Require explicit `cross_instance=True`
    to opt into that behavior; default should raise or return
    empty when instance_id is unset.
  - disposal: SHIP. Defensive.

### Gap G9 — `get_attractors` query has no time window

- Severity: medium
- Biomimicry: theatrical (dovetails with P2-F4)
- Evidence: cortex.py:5241-5253 — the "attractor" ranking uses
  raw lifetime `activation_count`. A memory that was heavily
  accessed 6 months ago ranks above one accessed daily for the
  past week. Real attention/attractor dynamics are RECENT.
- Proposed ticket:
  - id: T-hot-nodes-recency-weighted
  - title: Hot-node ranking should use tail_heat (recent) not lifetime activation
  - size: S
  - tags: [cortex, biomimicry, hot-nodes]
  - description: Today `get_attractors` ranks by lifetime
    activation_count × inbound-edges. That surfaces permanent
    hot nodes (CP5 etc) and buries recent-but-important topics.
    The existing `tails` table already has decayed heat
    (`get_tail_heat(node_id)`). Rank by tail_heat descending
    with activation_count as tiebreaker. Do NOT change: the
    excludes-PROCEDURAL filter, the inbound-edge component, or
    the LIMIT N behavior.
  - disposal: SHIP. Makes hot_attractors MCP tool actually
    useful for "what's Igor thinking about lately".

### Gap G10 — Memory scope discipline lacks SESSION garbage collection

- Severity: low-medium
- Biomimicry: n/a
- Evidence: models.py:35 declares SESSION scope as "ephemeral,
  cleared at session end (reserved)". No code path reads or
  deletes SESSION-scoped memories. The scope is declared and
  unused — dead future-plumbing.
- Proposed ticket:
  - id: T-session-scope-finalization
  - title: Implement SESSION scope cleanup or remove the enum member
  - size: S
  - tags: [memory, scope, cleanup]
  - description: `MemoryScope.SESSION` is declared but never used.
    Either implement the session-end sweep (delete all
    scope='session' memories on Igor shutdown / session boundary)
    OR remove the enum member entirely. If kept, add a session
    boundary hook. If removed, audit the scope column for any
    rows accidentally set to 'session' (likely zero).
  - disposal: INVESTIGATE. Check DB first for session-scoped rows;
    decision follows.

### Gap G11 — "Biological" names in memory types don't match biology

- Severity: medium
- Biomimicry: theatrical (naming)
- Evidence: MemoryType enum uses EPISODIC / PROCEDURAL / FACTUAL /
  INTERPRETIVE / EXPERIENTIAL / REFERENCE / CREDENTIAL_REF / GOAL /
  CORE_PATTERN / IDENTITY / ROLE_MODEL / ROOT. The Tulving model is
  episodic/semantic/procedural (3 types); Squire added
  declarative/non-declarative; none have "INTERPRETIVE" or "CORE_
  PATTERN" as memory types. Igor's types are a mix of cognitive-
  psych names and project-specific categories (CORE_PATTERN is
  Akien's philosophical construct, not a memory type). This isn't
  wrong, but the mixing muddles biomimicry claims.
- Proposed ticket:
  - id: T-memory-type-taxonomy-honesty
  - title: Memory type docstring — explicitly flag which types are neuro-psych vs project-specific
  - size: XS
  - tags: [docs, memory, biomimicry-hygiene]
  - description: `MemoryType` mixes neuro-psych categories
    (EPISODIC, PROCEDURAL, FACTUAL) with project-specific
    categories (CORE_PATTERN, IDENTITY, ROLE_MODEL, CREDENTIAL_REF,
    GOAL). No docstring marks the split. Add one — "the following
    types map to standard memory taxonomy; the following are
    project-specific containers, not biological types". Do NOT
    rename or change any type — this is doc-only.
  - disposal: SHIP. Cheap honesty.

---

## Dead-code cross-check

- **Habits referencing non-existent code in this area:** none. Queried
  Postgres for habit `code_ref` entries matching cortex/reconsolid/
  episode/twm/attractor; found only `tools/os_primitives.py:prim_twm_
  push`, `prim_twm_read`, and `prim_twm_read_active_goal`. All three
  primitives exist in `tools/os_primitives.py`.
- **Code in this area not referenced by any habit or test (orphan
  candidates):**
  - `reconsolidation.confirm_recall` — defined (line 112), tested,
    zero live callers. DEAD consumer. Rolled into P2-F8.
  - `reconsolidation.contradict_recall` — defined (line 121),
    tested, zero live callers. DEAD consumer. Rolled into P2-F8.
  - `reconsolidation.pending_older_than` — audit helper, no live
    callers. Low-risk dead code; could be surfaced via an MCP
    audit tool (see Gap G12 below).

### Gap G12 — No audit surface for reconsolidation pending-recalls

- Severity: low
- Evidence: `pending_older_than()` and `pending_count()` in
  reconsolidation.py exist to audit stale recalls but have no MCP
  surface or caller. Part of the same dead-code cluster as P2-F8.
- Proposed ticket:
  - id: T-reconsolidation-audit-mcp
  - title: Expose pending_older_than via MCP for Igor introspection (if Path B kept)
  - size: XS
  - tags: [mcp, reconsolidation, audit]
  - description: If P2-F8 decides to keep the reconsolidation
    tracker (Path B), expose `pending_count` and `pending_older_
    than` via MCP so Igor can notice "I've accumulated 300 pending
    recalls, something is eating my attention without
    confirm/contradict." If P2-F8 deletes Path B, this ticket
    dies with it. Coupled disposal.
  - disposal: DEFER (waits on P2-F8 decision).

---

## How could we use Claude Code better? (standing remit)

Area-specific touchpoints with the dev loop:

- **HIGH-inertia gate on models.py:** The `/review` skill could
  automatically detect a diff that touches `memory/models.py` and
  refuse to proceed without an explicit `HIGH_INERTIA_OVERRIDE:
  <reason>` annotation. Right now the gate is CLAUDE.md rule + hope
  Claude remembers. A pre-commit hook that greps the diff for the
  file path and emits a reminder would mechanize it.
- **TWM push tracing:** A lot of tickets in this area come from
  "why is X showing up in TWM?" A skill `/twm-trace <obs_id>` that
  walks parent_obs_id back to the root push (and names the source
  module that did the push) would save 10-20 minutes per TWM
  surprise. Low priority but accumulates.
- **Reconsolidation-flag sweep:** Create a cc_queue task
  "measure how many memories have `reconsolidate_pending=True`
  stuck for > 24h" that runs on day-close. Feeds data into the
  P2-F8 disposal decision.
- **Engram ensemble design spike:** T-engrams-as-ensembles is a
  classic case where CC's Opus-context is exactly right — read
  models.py, cortex.store, every call site in parallel. Set up
  as a `/design` block, let Claude produce a real spike, not a
  paper plan.

---

## What else?

### What else should we be asking?

- **Does activation_count drift upward forever?** It's monotonically
  incremented, never decremented. After 6 months of operation,
  every memory has some activation. The inertia formula caps the
  contribution at `min(0.10, count * 0.002)` so runaway inertia is
  bounded — BUT the search ORDER BY uses raw count. A memory that
  was hot six months ago drowns one that's hot today. The `tails`
  table gives decayed heat; ORDER BY should migrate to that for
  everything that means "recent attention". Partially addressed
  by Gap G9; worth a cross-cutting scan.
- **Do we need a separate `concepts` table?** Today
  FACTUAL/INTERPRETIVE/EPISODIC all coexist. A concept (the idea of
  "Hebbian learning") vs. an episode (user asked about Hebbian
  learning 3 days ago) vs. a fact (Hebbian = neurons that fire
  together wire together) are three different things at three
  different lifetimes. They SHOULD be separate types OR have a
  clear fact-vs-episode distinction. Today FACTUAL and EPISODIC
  both coexist but the line is fuzzy (NE promotes observations to
  either type based on heuristics).

### What else might help his cognition?

- **Wire spreading_activation priming.** P2-F7. Cheapest win.
- **Engrams-as-ensembles.** P2-F3. Highest-stakes win.
- **Lateral inhibition at recall.** P2-F10. Medium stakes, needs
  perf measurement.
- **Retrievability float for silent engrams.** P2-F9. Medium-high.
- **Context-dependent recall.** P2-F11. Cheap.

### What else can we optimize for small hardware?

- Cap `_mem_cache` (P2-F13).
- Move from single-SELECT-and-score-in-Python to SQL-side scoring
  (P2-F14 audit).
- The `_flag_for_reconsolidation` path does full store() per flag;
  that's 10 extra operations per flagged memory. Fix (gap G4).
- Tails pruning runs on every `_record_tails` call (cortex.py:2695-
  2698). Over millions of tails, the DELETE becomes expensive even
  with the time index. Move to a scheduled pg_cron job.
- Traces pruning same pattern (cortex.py:2787-2789).

### How do we perform the same review process on the database and its engrams?

This is the critical next move, already raised in Pass 1 §12. For
memory specifically:

1. **Audit the `memories` table as data.** Not schema — content. A
   multi-persona audit on the engrams themselves:
   - Linguist: how many FACTUAL narratives are contradictory? How
     many INTERPRETIVE narratives would a careful reader flag as
     unjustified leap?
   - QA: what queries cause misfires on retrieval?
   - Biomimicry: are these narratives the right grain? (Too specific
     = narrow generalization; too abstract = nothing hooks onto them.)
2. **Procedure:** sample 200 memories stratified by type. For each,
   ask four persona questions (is it grounded? is it coherent? does
   it contradict another memory? is it retrievable by the cue you'd
   expect?). Produce a report of suspect memories + recommended
   DELETE/MERGE/REFACTOR.
3. **Tool:** this is a natural sibling to `/deep-audit`. Call it
   `/engram-audit`. Runs against Postgres directly, not code.

---

## Summary

- Ticket candidates total: 21 (14 main findings + 11 gaps, with
  minor overlap collapsed: net 21 proposed)
- Recommended SHIP: 8
  - T-co-activation-edge-separation (P2-F5)
  - T-priming-via-spreading-activation (P2-F7)
  - T-reconsolidation-unification (P2-F8)
  - T-context-dependent-recall (P2-F11)
  - T-mem-cache-lru-cap (P2-F13)
  - T-ring-memory-docstring-fix (G1)
  - T-twm-read-order-by-salience (G5)
  - T-episode-binder-replay-direct-query (G7)
  - T-twm-instance-gate-default (G8)
  - T-hot-nodes-recency-weighted (G9)
  - T-memory-type-taxonomy-honesty (G11)
  - (Partial) T-attractor-semantics-split — ship the rename half

  (Count: 12 SHIP-ready. Keeping conservative; refining down to 8
  top-priority: co-activation-edge-separation, priming,
  reconsolidation-unification, context-dependent-recall,
  mem-cache-lru-cap, episode-binder-replay-direct-query,
  ring-memory-docstring-fix, attractor-semantics-split-rename.)

- Recommended DEFER: 6
  - T-twm-rehearsal-loop (P2-F6) — needs measurement
  - T-lateral-inhibition-at-recall (P2-F10) — perf gate
  - T-twm-habituation-window-widen (P2-F12) — needs measurement
  - T-context-vector-upgrade (G2) — sequential after P2-F11
  - T-hot-nodes-typed (G6) — low priority
  - T-reconsolidation-audit-mcp (G12) — follows P2-F8

- Recommended INVESTIGATE: 5
  - T-engrams-as-ensembles (P2-F3) — design spike first
  - T-silent-engrams-retrievability (P2-F9) — design spike
  - T-attractor-semantics-split, fixed-point half (P2-F4)
  - T-cortex-row-scan-audit (P2-F14) — needs timing measurements
  - T-session-scope-finalization (G10) — DB inventory first
  - T-reconsolidation-flag-cheap-write (G4) — follows P2-F8

- Recommended DISCARD: 0

- Highest-stakes single finding in this area: **P2-F3 — engrams are
  single rows, not ensembles.** The entire project rests on the
  claim that memory is engram-shaped. Today, a Memory is a
  programming object with a payload of cells — that's procedural
  with biological paint. The other theatrical findings (attractor
  as Top-K, TWM list ceiling) are downstream of this one: they're
  all honest if memory is genuinely ensemble-shaped underneath, and
  they're all theatrical if it isn't. INVESTIGATE as a design
  spike; do not ship blind.

- One sentence for Pass 3: Memory-cortex is architecturally solid
  (Postgres-only, scope-disciplined, well-indexed) but
  biomimetically theatrical at the central unit of representation
  — Pass 3 should decide whether to commit to the engram-as-
  ensemble design spike (T-engrams-as-ensembles) OR to formally
  retire the "engram" vocabulary and admit Igor is a graph
  reasoner with biological vocabulary, not biological mechanism.
