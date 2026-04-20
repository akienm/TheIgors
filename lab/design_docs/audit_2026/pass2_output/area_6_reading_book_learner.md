# Pass 2 deep-dive — READING + BOOK_LEARNER

Auditor: Opus 4.7 (1M context). Read-only. 2026-04-20.
Scope: wild_igor/igor/tools/reading_tool.py, reading_engine.py,
reading_integration.py, reading_measure.py, reading_benchmark.py,
ebook_reader.py, bootstrap_reader.py; lab/claudecode/book_learner.py,
reading_campaign.py, reading_integrator.py, drain_learn_queue.py,
cron_feed_reading.py, seed_watchlist.py; lab/tools/scan_ebooks.py;
wild_igor/igor/cognition/replay.py (FACT_CLOUD replay); watch engrams
(WATCH_Q_*, WATCH_T_* via seed_watchlist); reading_list table
(cortex.py:339–355).

---

## Per-finding verdicts

### Finding P1.1 — `book_learner._should_use_local` dangerous default (`except: return True`)

- Verdict: **CONFIRMED_NARROWER**.
  `lab/claudecode/book_learner.py:73–97`. The `except Exception: return
  True` is real, but the blast is narrower than Pass 1 suggested.
  `True` means "use local Ollama" — the *safer* default for this code
  path. Cost-wise this is the conservative failure. The risk Pass 1
  named ("silently force all reading to local") is, in this codebase,
  the *desired* default. HOWEVER — the function is theatrical in a
  different way: every single failure mode (file missing, JSON
  malformed, expired timestamp unparseable) collapses to the same
  "no override active" branch. You cannot distinguish "the override
  file is corrupt and Akien thinks cloud is on" from "the override
  simply isn't set". That IS a correctness hazard: Akien turns on
  cloud via `cloud_ok_override.json`, the file gets truncated by a
  crashed writer, book_learner silently reverts to local, Akien
  never knows.
- Blast radius: `_should_use_local` is called once per chunk
  (line 1117, 1128). `drain_learn_queue._is_cloud_ok_override` is a
  parallel implementation of the same check (duplication — cross-cut
  with persona 1). The `cloud_ok_override.json` file is touched by
  multiple processes with no locking. No tests exist for the
  corrupted-JSON path.
- Biomimicry: n/a — this is pure ops/cost gating.
- Proposed ticket:
  - id: T-cloud-ok-override-fail-loud
  - title: cloud_ok override — fail loud on parse error, not silent
  - size: S
  - tags: [reading, ops, cloud-budget, safety]
  - description: `_should_use_local()` today collapses every
    exception into "use local" (the safe default). That hides a
    real failure mode: a corrupted `~/.TheIgors/cloud_ok_override.json`
    (partial write, invalid JSON, bad expires timestamp) looks
    identical to "no override set" and Akien's explicit cloud-on
    intent is silently ignored. The fix shape: split the exception
    funnel into (a) FileNotFoundError → silent local (correct),
    (b) JSON/timestamp parse failure → log ERROR via forensic_logger
    AND push a TWM observation `CLOUD_OVERRIDE_CORRUPT|<path>` so Igor
    notices on next turn, then local. Duplicate the same shape into
    `drain_learn_queue._is_cloud_ok_override` (single source of
    truth would be even better — extract to
    `igor.cognition.cloud_mode:is_cloud_ok_override()` and import
    from both sites). Files touched: `lab/claudecode/book_learner.py`,
    `lab/claudecode/drain_learn_queue.py`, optionally a new
    `wild_igor/igor/cognition/cloud_mode.py` (de-dup). NOT
    changed: the semantics of "on error, use local" — that stays.
    Not HIGH inertia. Old duplicated code path safe to delete once
    both callers migrate.
  - **Disposal: SHIP.**

### Finding P1.2 — `book_learner` `sys.path.insert` into wild_igor (boundary violation)

- Verdict: **CONFIRMED_WORSE**. Pass 1 named one site. It's actually
  three:
  - `lab/claudecode/book_learner.py:47–49`: `sys.path.insert(0, REPO)` +
    `sys.path.insert(0, REPO / "wild_igor")` at module import time,
    unconditional.
  - `wild_igor/igor/tools/reading_tool.py:581–582` (worker script
    heredoc): the `_ensure_worker_script` writes a subprocess that
    itself `sys.path.insert`s into both repo and wild_igor.
  - `wild_igor/igor/tools/reading_engine.py:203–205, 323–325`:
    `process_one_chunk` and `process_blob` do `sys.path.insert` at
    call time to reach into `lab/claudecode/book_learner` — the
    REVERSE direction, wild_igor reaching out to lab. So the
    boundary is violated in BOTH directions, which is worse than
    Pass 1 said.
  - Fourth site: `lab/claudecode/reading_campaign.py:573–575` does
    `from wild_igor.igor.tools.reading_engine import ...` — works
    only because of an earlier path insert somewhere up the stack.
- Blast radius: any test harness that runs `book_learner.py` from
  a different cwd gets a silent fail. Pre-commit `ruff` cannot find
  the imports without the insert. Packaging as a wheel is impossible
  — `lab/` and `wild_igor/` have to be installed as a single blob.
  More subtly: when wild_igor imports lab (the reverse direction),
  a worker running under the Igor runtime can pick up *stale* lab
  code, because lab isn't on the permanent path — it's sys.path-
  injected per call, and module caching means the first-imported
  version wins for the life of the process. This is a real source
  of "why didn't my edit take effect?" confusion. Cross-cut with
  persona 2 (architecture).
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-reading-lab-wildigor-boundary
  - title: reading pipeline — remove sys.path hacks, define boundary
  - size: L
  - tags: [reading, architecture, boundary, refactor]
  - description: `book_learner`, `reading_tool`, `reading_engine`,
    `reading_campaign` form a tangled import graph that violates
    the `lab/` vs `wild_igor/` separation in both directions. Four
    sys.path.insert sites. The shape of the fix:
    (a) move extraction prompts (`_EXTRACT_PROMPT`, `_EXTRACT_PROMPT_PASS2`,
    `_build_watch_context`), node-deposit logic (`_deposit_nodes`,
    `_arousal_from_cp`, `_score_attractor_overlap`), and spine
    helpers (`_ensure_book_node`, `_ensure_chapter_node`,
    `_deposit_completion_record`) INTO `wild_igor/igor/tools/
    reading_engine.py`. Those functions have no business living in
    `lab/` — they're the runtime deposit machinery, not the CLI
    wrapper. (b) reduce `book_learner.py` to a thin CLI shim that
    imports from `wild_igor.igor.tools.reading_engine` and
    `wild_igor.igor.tools.book_learner_cli`. (c) install wild_igor
    as an editable pip install (`pip install -e wild_igor/`) so
    sys.path.insert can die. (d) `reading_campaign.py` imports the
    new canonical path. NOT changed: the lab-side progress files
    (`PROGRESS_DIR`), the reading_worker.py subprocess pattern
    (that's a legit runtime arg), the prompt TEXT itself. This is
    a structural move — nontrivial — but unblocks tests, packaging,
    and mental model. Old sys.path.insert lines safe to delete
    only after (c) ships. Not HIGH inertia but touches 4 files.
  - **Disposal: DEFER.** Pre-req for packaging but not urgent if the
    goal is to keep Igor running on akiendelllinux. SHIP when CC
    bandwidth allows or when the stale-module-cache bug actually
    bites.

### Finding P1.3 — `_deposit_nodes` is N+1 cortex.store calls; add_child / add_interpretive_edge further N+1s

- Verdict: **CONFIRMED**. `book_learner.py:833–955`. The per-node
  loop does:
  1. `cortex.store(mem)` (line 919) — 1 INSERT
  2. `cortex._get_or_compute_embedding(mem)` (line 923) — 1 embedding
     call, possibly 1 more INSERT into `memory_embeddings`
  3. `cortex.add_child(parent_cp, uid)` (line 930) — write
  4. `cortex.add_interpretive_edge(parent_cp, uid, ...)` (line 934) —
     write (this one hits `interpretive_edges` table)
  5. `cortex.add_child(chapter_node_id, uid)` (line 948) — write
  That's up to 5 DB round-trips per deposited node. For a 200-chunk
  book with ~3 nodes per chunk, that's 3000 round-trips. On a busy
  embedding model (qwen on CPU), the sequential embedding calls in
  step 2 are the tallest pole. Pass 1 got this right.
- Blast radius: reading throughput ceiling. A campaign against the
  whole reading_list (~hundreds of books) at current speed is
  probably multi-week. This is the single biggest reason reading
  feels slow. The `reading_engine.process_blob` wrapper compounds
  this — same loop again with an outer `time.sleep(delay)`
  (line 450) between chunks on top of the N+1.
- Biomimicry: **theatrical**. Pass 1 didn't flag it as theatrical
  but it is. Reading-as-densification (the load-bearing claim in
  `reading_tool.py`'s docstring) is supposed to strengthen a
  network. In reality it's serial INSERTs with arousal scores
  stamped at deposit time. A biological reader would activate a
  *distributed ensemble* per concept, with co-activation strengths
  falling out of the firing pattern — not a per-node-per-edge
  round-trip. The honest version: a single batch deposit op that
  takes (nodes[], edges[], embeddings[]) and issues three bulk
  `COPY` or multi-VALUES INSERTs per chunk, letting Postgres do
  the work. The spreading activation / co-occurrence *emerges* in
  a second pass that reads many nodes at once and writes edge
  updates in aggregate (see `replay.py` — that module is closer to
  the honest mechanism, but it only runs in quiet periods and
  it's per-pair not per-cluster).
- Proposed ticket:
  - id: T-reading-deposit-batched
  - title: reading deposit — one transaction per chunk, not per node
  - size: M
  - tags: [reading, performance, db, biomimicry]
  - description: `_deposit_nodes` currently issues up to 5 DB
    round-trips per deposited node. For a chunk with 3 nodes,
    that's 15 round-trips, plus the (often dominant) serial
    embedding calls. Shape of the fix: (a) batch the `cortex.store`
    calls into a single transaction per chunk — `with
    cortex._conn() as conn: conn.execute("BEGIN"); for mem in ...;
    conn.execute("COMMIT")`, or use psycopg2's `execute_values`
    for the INSERT. (b) batch `add_child` edges into one
    multi-VALUES INSERT into `clan.memories` parent_id updates or
    whatever the edge table is. (c) batch `add_interpretive_edge`
    the same way. (d) compute embeddings in a parallel thread-pool
    inside the chunk (N embedding calls concurrent rather than
    serial) — or defer embedding to the `consolidation_replay` /
    `reading_integrator` second pass so the hot-path deposit is
    pure INSERT. NOT changed: the per-node *logic* — what's
    extracted, what arousal is assigned, what CP is mapped. NOT
    changed: backward-compat of the node schema. Expect a 3–10×
    throughput improvement on hot campaigns. Files: primarily
    `lab/claudecode/book_learner.py` (or
    `wild_igor/igor/tools/reading_engine.py` if T-reading-lab-
    wildigor-boundary lands first), plus `Cortex` may need a new
    `store_batch()` / `add_children_batch()` method.
    **HIGH-INERTIA FLAG**: this touches `memory/cortex.py` — Akien
    must review batch semantics (does a partial failure leave a
    half-written spine? what's the rollback story?).
  - **Disposal: SHIP.** Highest-leverage single change in this area.

### Finding P1.4 — `_arousal_from_cp` is theatrical procedural arousal vs the systemic milieu

- Verdict: **CONFIRMED_WORSE**. `book_learner.py:617–625`. It's a
  keyword-hit counter clamped to [0.10, 0.60], with a static 6×7
  keyword dictionary (line 607–614). Pass 1 named this as a "LIE";
  I confirm and escalate. Three reasons it's worse than Pass 1 said:
  1. **Stamped at deposit, never revisited.** The arousal value
     becomes a column on the Memory row. The milieu moves
     continuously (`wild_igor/igor/cognition/milieu.py` is the
     honest VAD model). A node deposited with arousal=0.23 is
     stuck at 0.23 forever — Igor's actual arousal at reading
     time has no coupling to the stored value, and his arousal at
     *retrieval* time doesn't modulate the retrieval either. This
     is "theatrical" *and* "decoupled from the real signal".
  2. **It's called "arousal" but it's a CP-affinity score.** CP
     affinity is roughly "which cornerpost does this concept
     resonate with" — that's a categorical classification, not
     an arousal level. Calling it arousal overloads a real
     systemic term with a keyword-hit count.
  3. **Parallel implementation.** `lab/claudecode/reading_integrator.py:
     70–95` has `_best_cp` with the *same* keyword dictionary.
     Two copies, same data, drift risk. Cross-cut with persona 1
     (code hygiene, duplication).
- Blast radius: every book_learner deposit since this landed has a
  fake-arousal column. Downstream code that reads `memory.arousal`
  (e.g., cortex ranking?) is getting a keyword-bigram relevance
  score wearing the arousal label. Narrative engine that surfaces
  high-arousal memories is surfacing high-keyword-density memories.
  Silent misdirection.
- Biomimicry: **theatrical** (confirmed). Honest mechanism sketch:
  at deposit time, sample the current milieu state
  (`milieu.read_state()`) and stamp THAT as `encoding_arousal` —
  Igor's actual arousal when he read the passage. Separate field
  for CP affinity called `cp_affinity` or `identity_weight`
  (which already exists in the metadata — so the column is just
  mislabeled). On retrieval, modulate by *current* milieu arousal
  (state-dependent retrieval is a real cognitive phenomenon). The
  honest version changes arousal from "what the text is about" to
  "what Igor's state was when he read it and what it is now" —
  which is what arousal actually means in the biology.
- Proposed ticket:
  - id: T-reading-arousal-honest
  - title: reading arousal — stamp current milieu, not keyword hits
  - size: M
  - tags: [reading, biomimicry, milieu, memory]
  - description: `_arousal_from_cp()` computes a keyword-hit score
    against a 6×7 CP dictionary and stamps it as `arousal` on the
    deposited memory. This is theatrical: it's a CP-affinity
    relevance score, not arousal in the systemic sense that
    `milieu.py` models. Shape of the fix: (a) at deposit time,
    sample `milieu.read_state()` and stamp its arousal component
    as `encoding_arousal` — this is Igor's actual systemic arousal
    at the moment of reading. (b) keep the keyword-hit score but
    rename/move it to `cp_affinity` in metadata (it's already half
    there as `identity_weight`). (c) at retrieval, introduce a
    modulation: `retrieval_score *= f(current_arousal -
    encoding_arousal)` — state-dependent recall. (d) delete the
    duplicated `_best_cp` / `_CP_KEYWORDS_AROUSAL` in
    `reading_integrator.py`. NOT changed: the keyword dictionary
    itself (still useful as a CP-affinity signal, just renamed).
    NOT changed: the deposit happening at all. This is a semantic
    correction + a hook into the real arousal system. Pairs well
    with T-reading-deposit-batched. Files:
    `lab/claudecode/book_learner.py`,
    `lab/claudecode/reading_integrator.py`,
    `wild_igor/igor/cognition/milieu.py` (may need a
    `read_state()` accessor if one doesn't exist),
    `wild_igor/igor/memory/models.py` (NEW column or doc'd
    reuse of existing `arousal` field — **HIGH-INERTIA**, Akien
    review). Not safe to delete old code until downstream readers
    of `memory.arousal` are audited — the field is load-bearing.
  - **Disposal: SHIP.** This is the highest-value biomimicry
    correction in the area. Moves the system from theatrical to
    honest on a central claim.

### Finding P1.5 — `scan_ebooks.py` hardcodes `/home/akien/.TheIgors/akien/onedrive/...`

- Verdict: **STALE** (partial). Pass 1 cited
  `wild_igor/igor/tools/scan_ebooks.py`. That file does NOT exist
  in wild_igor/igor/tools/ — the live version is at
  `lab/tools/scan_ebooks.py:32–35`. The `wild_igor/igor/tools/`
  has been cleaned up (the hardcoded version is gone from the
  runtime path). Finding is still real for the lab-side copy but
  narrower in scope — this is a CC-dev-loop script, not a live
  Igor tool. Meanwhile `wild_igor/igor/paths.py:190–237` correctly
  defines `ebooks_root`, `calibre_library`, `kindle_dir` with
  platform branches and env override — the *correct* abstraction
  already exists; `scan_ebooks.py` just doesn't use it.
  Also still hardcoded: `lab/claudecode/calibre_catalog.py:477`
  has a hardcoded `/home/akien/.TheIgors/akien/onedrive` fragment.
- Blast radius: narrow — `scan_ebooks.py` is an Akien-run dev
  script, not Igor-run. Portability is affected for any future
  second-machine install. Cross-cuts persona 11's broader hardcoded-
  path theme.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-scan-ebooks-use-paths
  - title: scan_ebooks + calibre_catalog — use paths().ebooks_root
  - size: S
  - tags: [ops, portability, paths]
  - description: `lab/tools/scan_ebooks.py:32–35` and
    `lab/claudecode/calibre_catalog.py:477` hardcode
    `/home/akien/.TheIgors/akien/onedrive/...` despite
    `wild_igor/igor/paths.py:190–237` already providing the
    correct abstraction (`paths().ebooks_root`,
    `paths().calibre_library`, with platform branches and
    `EBOOKS_ROOT` / `CALIBRE_LIBRARY_PATH` overrides). Shape of
    the fix: replace the hardcoded Path objects with
    `from wild_igor.igor.paths import paths; CALIBRE_DB =
    paths().calibre_library / "metadata.db"; EBOOKS_ROOT =
    paths().ebooks_root`. No logic change. NOT changed: the
    classification heuristics, priority tiers, output format.
    Two small files. Old hardcoded lines safe to delete
    immediately.
  - **Disposal: SHIP.** Cheap, unblocks portability, a clean
    hygiene win.

---

## Pass 1 gaps (findings Pass 1 missed in your area)

### Gap 1 — Reading-as-densification does not measurably densify

- Severity: **critical**
- Biomimicry: **theatrical**
- Evidence: The load-bearing claim in `reading_tool.py:17–27`
  ("reading is the primary densification mechanism … Cloud
  escalations drop when the reader has already paved paths through
  a concept") has NO closed-loop measurement. `reading_measure.py`
  exists as a before-snapshot tool (`reading_graph_baseline()`) but
  I find no after-snapshot code that compares the baseline to a
  post-reading state. There is no metric for "did reading X
  actually reduce cloud escalation rate by Y%". The claim
  rests on theoretical plausibility ("denser graph ⇒ more
  traversable ⇒ fewer cloud calls") without the feedback loop
  that would prove it. This matters because if the claim is
  FALSE — if the deposited FACT_CLOUD nodes don't actually get
  retrieved at answer time — then the whole reading pipeline is
  cognitive theater. `tests/test_consolidation_replay.py` tests
  that edges are created; it does not test that edges are
  TRAVERSED.
- Cross-cut with persona 3 (DBA: "the heavy reliance on the
  database for inter-process communication will become a
  bottleneck") and persona 9 (systems dynamics: "Missing
  Feedback Loops: Cost → Habit Compilation").
- Proposed ticket:
  - id: T-reading-densification-closed-loop
  - title: reading — measure "does it actually densify" end-to-end
  - size: L
  - tags: [reading, biomimicry, measurement, feedback-loop]
  - description: Igor's reading pipeline is justified by
    "reading densifies the graph, reducing cloud escalation". This
    has never been measured end-to-end. Shape of the fix: (a)
    `reading_measure.py` already captures pre-baseline; add a
    `reading_graph_after()` that runs the same query post-campaign.
    (b) instrument `cortex.search` / `inference_gateway.call` to
    log, for each query, (matched_node_ids, had_to_escalate_to_cloud).
    (c) for each book deposit, the `READING_<hash>` completion
    node gets a post-hoc `retrieval_hits` counter that increments
    every time one of its deposited nodes is surfaced in a
    subsequent search. (d) a weekly report: "book X deposited N
    nodes, M of them retrieved at least once in the last 7d,
    average retrieval latency, escalation rate on queries that
    matched X's nodes vs queries that didn't". (e) use this as
    the signal for which books to re-read (pass-2 situated reading
    on retrievable nodes, skip on silent ones). NOT changed: the
    deposit pipeline itself. This is pure instrumentation + a
    quiet-period report. The payoff: the first time a book shows
    "0 nodes retrieved in 30 days" Igor can propose deleting the
    deposits — closing the loop the pipeline was built to close.
    Touches `reading_measure.py`, `cortex.py` (instrument search),
    `inference_gateway.py` (log escalations). **HIGH-inertia
    flag**: `cortex.search` instrumentation touches a hot path.
    Akien review for perf.
  - **Disposal: INVESTIGATE.** The measurement infra is worth
    building; the remediation actions (delete silent nodes, etc.)
    are decision-calls for Akien. Defer the action, ship the meter.

### Gap 2 — Watchlist filter is advertised as a gate but is not a gate

- Severity: **high**
- Biomimicry: **procedural-with-bio-name**
- Evidence: `reading_tool.py:61–69` docstring says "the watchlist
  filter decides 'is this worth keeping?' BEFORE the deposit step.
  Things Igor actively cares about … pass the filter; generic
  sentences get summarized or dropped." Read the actual code:
  `book_learner.py:807–830, 843–902` — the watchlist keywords are
  pulled, an `attractor_score` is computed, and then lines 843–848
  explicitly say "is NO LONGER a deposit gate … every book yields
  something; low-relevance nodes get low scores and decay naturally
  through activation dynamics". So the watchlist ONLY modulates
  `identity_weight` (0.2 / 0.5 / 0.8 bands), it does not filter.
  The docstring is lying about the mechanism. Separately — the
  "decay naturally through activation dynamics" rationale is itself
  theatrical: deposited low-weight nodes sit in the graph being
  retrieved at zero rate, and the "natural decay" is just the ORDER
  BY in attractor queries never surfacing them. There's no actual
  GC. Cross-cut with Gap 1 — this compounds the densification-
  without-densification problem.
- Proposed ticket:
  - id: T-watchlist-actually-gate
  - title: watchlist — decide whether it's a gate, then commit
  - size: M
  - tags: [reading, watchlist, engrams, honesty]
  - description: The reading subsystem's top-of-file docstring
    says the watchlist filter GATES deposits. The code merely
    modulates `identity_weight`. Either the docstring is wrong
    or the code is. Akien's 2026-04-18 principle cited inline
    ("there's nothing I read that I don't get anything at all
    from") argues for the current behavior (no hard gate). If so,
    the docstring in `reading_tool.py:61–69` needs to say that.
    If the gate SHOULD exist — e.g., for books that are clearly
    off-topic pulp — then the 0.0 lower band should be "reject",
    not "deposit at weight 0.2". Shape: (a) Akien-decision first
    (SHIP only after). (b) fix the lie wherever it lands —
    either the docstring or the code. (c) introduce honest GC:
    if a deposited FACTUAL node reaches N days with 0 retrievals
    AND identity_weight < 0.3, archive (not delete — move to
    cold storage) it. This is the missing "natural decay" the
    code promises. Cross-couples with Gap 1 (the measurement
    makes the decay safe). Files:
    `wild_igor/igor/tools/reading_tool.py` (docstring),
    `lab/claudecode/book_learner.py` (maybe code), optional
    new `wild_igor/igor/cognition/memory_gc.py`. Old docstring
    text safe to delete immediately after decision.
  - **Disposal: INVESTIGATE.** Requires Akien decision before
    writing code.

### Gap 3 — Calibre 8-tier arousal (D252) is nowhere in the code

- Severity: **medium**
- Biomimicry: **procedural-with-bio-name** (the tier name is
  biological; the implementation is absent)
- Evidence: Your prompt cites D252 (Calibre 8-tier arousal) as in-
  scope. I grep'd the codebase: 0 hits for "8-tier arousal",
  "calibre_arousal", "arousal_tier", "8_tier". `scan_ebooks.py`
  classifies into 7 priority tiers (P0 through P5 plus SKIP) — a
  priority ladder, not an arousal ladder. `reading_list.encoding_arousal`
  is a `REAL DEFAULT 0.5` — one column, not 8 bins. The D252
  decision, whatever its final form, is not implemented. Either
  the decision was retracted and not logged, or the implementation
  never landed. Cross-cut: this is related to T-reading-arousal-
  honest above — resolving both together is probably cheaper than
  separately.
- Proposed ticket:
  - id: T-calibre-8tier-arousal-or-retract
  - title: Calibre 8-tier arousal (D252) — implement or retract
  - size: S
  - tags: [reading, calibre, decisions, audit]
  - description: D252 is cited in the audit scope as "Calibre
    8-tier arousal". The code has 7-tier priority classification
    and a single-float arousal column. The 8-tier model is not
    implemented. Two paths: (a) if D252 is still intended,
    implement 8 discrete bins — probably {dismiss, skim,
    foreground-light, foreground-deep, bootstrap, urgent,
    re-read, cornerpost} — each with its own read-rate budget
    and model tier routing. Fold into `scan_ebooks.classify()`.
    (b) if D252 was abandoned, file the retraction in the
    decisions_log and scrub the reference from the audit scope.
    Shape assumes (a): extend `reading_list` schema
    (`arousal_tier TEXT`), expand `classify()` to emit a tier,
    let `book_learner` / `reading_campaign` route by tier. NOT
    changed: existing `encoding_arousal` float column stays for
    continuity. This is a small ticket but needs the
    retract/implement decision first. Files:
    `lab/tools/scan_ebooks.py`, `lab/claudecode/reading_campaign.py`,
    `wild_igor/igor/memory/cortex.py` (schema).
  - **Disposal: INVESTIGATE.** Akien decision first. If retract,
    this is a S/trivial. If implement, it's a small-M ticket.

### Gap 4 — Multiple reading-pipeline entry points, unclear canonical path

- Severity: **medium**
- Biomimicry: n/a
- Evidence: Reading can be initiated through any of:
  1. `reading_tool.reading(command="start_run")` — the canonical
     one per reading_tool's docstring.
  2. `lab/claudecode/book_learner.py` CLI — still the underlying
     worker.
  3. `lab/claudecode/reading_campaign.py worker_loop()` — the
     "real" batch path with budget + block queue.
  4. `wild_igor/igor/tools/bootstrap_reader.py start_reading_bootstrap()` —
     the high-quality-Sonnet path.
  5. `wild_igor/igor/tools/learner.feed_reading_list()` — bridges
     `reading_list` → `learn_queue.json`.
  6. `lab/claudecode/drain_learn_queue.py` — drains `learn_queue.json`
     by spawning book_learner subprocesses.
  7. `wild_igor/igor/tools/ebook_reader.start_foreground_reading()` —
     D107 sentence-by-sentence UI path.
  8. `IGOR_READING_EXTRACT=true` env var gate in
     `ebook_reader.read_chunk()` — silent G54 extraction path.
  9. `lab/claudecode/reading_integrator.py` — second-pass
     post-processing.
  Which is canonical? The docstring says `reading_tool`. The
  batch budget path is `reading_campaign`. The legacy cron path
  is `learner.feed_reading_list` → `drain_learn_queue`. These
  don't compose cleanly — they're three alternative pipelines,
  each partially implemented, each with its own state machine.
  A new reader (human or AI) has to read ~8 files to find out
  how to "read a book". Classic organically-grown architecture.
  Cross-cut with persona 2 (architect), persona 11 (docs).
- Proposed ticket:
  - id: T-reading-entry-points-canonicalize
  - title: reading — pick ONE canonical entry point, deprecate rest
  - size: M
  - tags: [reading, architecture, docs-in-code, cleanup]
  - description: Reading has 9 entry points (enumerated above).
    The docstring says `reading_tool.reading()` is canonical;
    the actual working batch path is `reading_campaign.worker_loop()`;
    the legacy cron path is `feed_reading_list → drain_learn_queue`.
    A new reader can't tell which to use. Shape of the fix:
    (a) Akien picks the canonical: probably
    `reading_tool.reading(command="start_run")` dispatches to
    `reading_campaign.worker_loop()` underneath for batch work.
    (b) `drain_learn_queue.py` + `learn_queue.json` retired
    (they predate the block queue). (c) `bootstrap_reader` kept
    as a mode override flag on the canonical path, not a
    separate tool. (d) `ebook_reader.start_foreground_reading`
    kept as the interactive-UI path (different purpose, not a
    batch reader). (e) `reading_integrator` folded into
    `consolidation_replay` OR called as the "pass 2" stage of the
    canonical path. (f) Update the `reading_tool.py` docstring
    (the pilot canonical doc) to name all 9 paths with
    retirement status for each. NOT changed: the underlying
    extraction logic, progress files, completion records. This
    is pure flow-of-control cleanup. Safe to delete retired
    entry points once the canonical path proves itself over a
    week of live traffic. Files: all 9 entry-point files plus
    the pilot docstring. Not HIGH-inertia but wide.
  - **Disposal: DEFER.** Depends on T-reading-lab-wildigor-
    boundary and T-reading-deposit-batched landing first. Pick
    canonical once the pipeline is clean enough to consolidate.

### Gap 5 — 300s → "no timeout" change hides a hang

- Severity: **medium**
- Biomimicry: n/a
- Evidence: `book_learner.py:490–498` comment block cites
  T-remove-extract-timeout (2026-04-19) and removes the urlopen
  timeout, with the rationale "slow on slow resources is ok, no
  timeouts for training/bulk-reading workloads … Hang safety
  will come from the worker pool (T-reading-worker-pool) at a
  higher level". Reading the higher level:
  `reading_campaign.worker_loop` has NO per-block timeout — it
  calls `_process_block_local` → `process_one_chunk` →
  `_extract_nodes_local` → `urllib.request.urlopen` with no
  timeout. One hung Ollama call blocks the worker loop
  indefinitely. The cited "higher-level safety" does not exist.
  Cross-cut with persona 4 (resource leaks), persona 10 (QA —
  "tests passing by accident").
- Proposed ticket:
  - id: T-reading-hang-safety
  - title: reading — add higher-level hang safety (promised, missing)
  - size: S
  - tags: [reading, ops, safety, worker-pool]
  - description: `book_learner._extract_nodes_local` removed its
    300s urlopen timeout on 2026-04-19 with the explicit promise
    "hang safety will come from the worker pool at a higher
    level". The worker pool (`reading_campaign.worker_loop`) has
    no timeout on its calls to `process_one_chunk`. One hung
    qwen call = dead worker. Shape of the fix: add a per-block
    wall-clock timeout in `worker_loop` — either wrap
    `_process_block_local` in `concurrent.futures` with a
    timeout (e.g., 600s per block; configurable via env), or
    restore the urlopen timeout with a much larger cap (e.g.,
    900s for qwen-on-CPU realism). On timeout: mark block
    `status='timeout'`, clear claimed_by, increment attempt,
    re-queue if `attempt_count < 3`, else `mark_block_failed`.
    NOT changed: the per-call no-timeout decision for interactive
    qwen calls — only the batch-worker path gets hang safety.
    Files: `lab/claudecode/reading_campaign.py`,
    `wild_igor/igor/tools/reading_engine.py` (process_one_chunk
    may need a timeout kwarg). Safe to add — no existing
    timeout to delete.
  - **Disposal: SHIP.** Promised and missing. Easy fix.

### Gap 6 — `_handle_key` cache lost on restart, recovery is theatrical

- Severity: **low-medium**
- Biomimicry: n/a
- Evidence: `ebook_reader.py:45` `_HANDLE_CACHE` is a module-level
  dict. `_resolve_handle` (line 664–690) tries to recover a
  cache miss by "reopening" from `reading_state.json` — but
  reopening a book takes ~seconds to minutes (epub parsing,
  NLTK tokenization). A foreground read_chunk request that
  hits a cache miss re-parses the whole book blockingly. Worse:
  in the stated "background worker" scenario, every worker
  spawn = fresh process = fresh empty `_HANDLE_CACHE` = re-parse
  cost on first chunk. `reading_engine.py:fetch_to_blob`
  actually AVOIDS this by going through its own blob cache,
  which is the honest approach. The ebook_reader handle cache
  is a leftover from the pre-blob era.
- Proposed ticket:
  - id: T-ebook-handle-cache-retire
  - title: ebook_reader — retire _HANDLE_CACHE in favor of blob cache
  - size: S
  - tags: [reading, ebook-reader, cleanup]
  - description: `ebook_reader._HANDLE_CACHE` is a module-level
    dict of BookHandle objects that dies on process restart and
    triggers expensive re-parse on miss. The blob cache in
    `reading_engine.fetch_to_blob` is the durable alternative —
    same data, on disk, survives restart, faster re-read.
    Shape of the fix: (a) in `ebook_reader.read_chunk` /
    `jump_to` / `reading_position`, check for an existing blob
    at `paths().reading_blobs / blob_key(source)` before falling
    back to the BookHandle cache. (b) if blob exists, read the
    sentences from there directly — skip the parse. (c)
    `_HANDLE_CACHE` becomes an optional hot-path cache only,
    backed by blobs on miss. (d) foreground reading (D107) gets
    free persistence for no extra code. NOT changed: the
    foreground UI, the `open_book` signature, the Calibre search.
    Safe to delete the cache-miss-reopen branch once blob
    fallback is in. Files: `wild_igor/igor/tools/ebook_reader.py`,
    `wild_igor/igor/tools/reading_engine.py` (minor). Not HIGH.
  - **Disposal: DEFER.** Nice-to-have optimization, not urgent.

### Gap 7 — reading_list table duplicated via coordination dance with memory graph

- Severity: **medium**
- Biomimicry: n/a
- Evidence: `reading_tool.py` stores run state as EPISODIC Memory
  nodes AND updates `reading_list` (lines 233–256, 489–496,
  641–651, etc.). The memory graph is described as "self-
  knowledge" and reading_list as "coordination". But the update
  pattern — every `_process_next` updates BOTH — creates a
  two-phase-commit problem: if the memory store succeeds and
  reading_list UPDATE fails (or vice versa), you get a
  READING_RUN node that says "complete" on a reading_list row
  that says "processing". No transactional boundary. Cross-cut
  with persona 2 (filesystem/db duality) and persona 3 (schema
  rationalization).
- Proposed ticket:
  - id: T-reading-state-consolidate
  - title: reading run state — one source of truth, not two
  - size: M
  - tags: [reading, db, consistency]
  - description: Reading run state is tracked in TWO places:
    EPISODIC memory nodes (`READING_RUN_...`) and the
    `reading_list` table (`status`, `claimed_by`, `completed_at`
    columns). Every state transition updates both. No
    transaction spans both writes. A crash mid-transition
    leaves them disagreeing. Shape of the fix: pick one as
    source-of-truth. Recommendation: the memory graph holds the
    *narrative* of the run; reading_list holds the *atomic
    claim lock* only. Reduce reading_list columns to just
    (source, run_id, claimed_by, claim_state ∈
    queued|processing|released) — no completed_at, no status
    beyond the claim lock. The rich status ("complete/failed/
    skipped", node_count, edge_count) lives on the Memory
    node, which is already the advertised model. `reading_list`
    becomes a narrow coordination primitive. NOT changed:
    multi-instance claiming (still FOR UPDATE SKIP LOCKED on
    reading_list). NOT changed: the Memory node shape. Files:
    `wild_igor/igor/tools/reading_tool.py`,
    `wild_igor/igor/memory/cortex.py` (schema). **HIGH-INERTIA
    flag**: cortex.py schema change, Akien review required.
    Old columns safe to delete after migration confirms no
    consumer reads them.
  - **Disposal: DEFER.** Worth doing, but not before T-reading-
    deposit-batched and T-reading-lab-wildigor-boundary.

### Gap 8 — `replay.py` FACT_CLOUD topology is SQLite-query-shaped

- Severity: **low**
- Biomimicry: honest (the intent), procedural (the query)
- Evidence: `wild_igor/igor/cognition/replay.py:128–140` queries
  `twm_observations` with `timestamp > ?` using `?` placeholder.
  The db_proxy does `? → %s` translation, but this module bypasses
  the proxy by calling `cortex._conn()` directly (line 126) which
  IS routed through the proxy. The placeholder is fine, BUT
  `replay.py:188` has `query += " AND timestamp > ?"` and
  `_run_replay` iterates groups doing `cortex.get()` + `cortex.store()`
  per pair (line 319, 337) — classic N+1. Compounds with the
  deposit N+1 in `_deposit_nodes`. This is the "honest" consolidation
  mechanism (per Pass 1 persona 5 finding: sleep consolidation is
  just clustering; `replay.py` is closer to honest), but its
  implementation shape is the same N+1 problem. One batch UPDATE
  to `interpretive_edges` would replace the whole inner loop.
- Proposed ticket:
  - id: T-replay-batch-edges
  - title: consolidation replay — batch edge updates, not per-pair
  - size: S
  - tags: [consolidation, replay, performance, biomimicry]
  - description: `ConsolidationReplay._upsert_edge` loads
    `cortex.get(src_id)`, mutates `.links`, and `cortex.store(src_mem)`
    for each pair. At `MAX_PAIRS_PER_PASS=50`, that's up to 100
    DB round-trips per replay pass. Shape of the fix: replace
    the pair loop with a single `INSERT ... ON CONFLICT DO
    UPDATE` batch statement against `interpretive_edges` (or
    whatever table backs `.links`). All pairs in one SQL call.
    Preserves the stats-tracking (edges_created vs
    edges_strengthened) via RETURNING clause. NOT changed: the
    grouping logic, the quiet-period gate, the cursor mechanism.
    Files: `wild_igor/igor/cognition/replay.py`. Low-risk —
    replay runs in a quiet period so the perf win is cosmetic,
    but it's also a cleaner implementation of the "replay
    strengthens co-activated ensembles" claim (that IS Hebbian
    when done in bulk; per-pair it's sequential reinforcement,
    which is less honest biology).
  - **Disposal: DEFER.** Low-priority perf win; bundle with a
    future replay touch.

### Gap 9 — DRM code path creates a silent "book read" with one DRM-notice sentence

- Severity: **low**
- Biomimicry: n/a (but amusing failure mode)
- Evidence: `ebook_reader.py:613–622` — when DRM decryption fails,
  the function returns `([f"[DRM-ENCRYPTED] Could not decrypt ...
  browse_as_employer..."], [0], ["DRM notice"])`. Downstream
  `book_learner` sees a book with 1 sentence, tokenizes it, extracts
  "nodes" from the DRM notice itself, and deposits a READING
  completion record for a book Igor never actually read. The
  completion record says "complete" because the 1 sentence was
  processed. This is a pristine "ghost book" in the self-knowledge
  graph.
- Proposed ticket:
  - id: T-drm-ghost-book-guard
  - title: DRM-failed books should not produce completion records
  - size: S
  - tags: [reading, drm, data-hygiene]
  - description: When DRM decryption fails in
    `ebook_reader._load_book_content`, the function returns a
    synthetic 1-sentence "book" containing a DRM notice. The
    reading pipeline happily processes that "book" and deposits
    a COMPLETION record claiming the book is read. Shape of the
    fix: (a) return a sentinel (e.g., raise
    `DRMDecryptionError` or return `(None, None, None)`) from
    the DRM branch. (b) `book_learner` / `reading_engine`
    recognize the sentinel and mark the item `failed` in
    reading_list with reason `drm_locked`, skip the deposit
    entirely. (c) file a FACTUAL memory `BOOK_DRM_BLOCKED_<hash>`
    so Igor knows the book exists but is walled off — this is
    correct self-knowledge. NOT changed: the DRM decrypt
    attempt itself, the browse_as_employer fallback hint.
    Files: `wild_igor/igor/tools/ebook_reader.py`,
    `lab/claudecode/book_learner.py`,
    `wild_igor/igor/tools/reading_engine.py`. Old sentinel text
    safe to delete once the sentinel-value flow is in.
  - **Disposal: SHIP.** Small and fixes a real data-quality
    failure.

### Gap 10 — Watchlist keyword union loses specificity

- Severity: **low-medium**
- Biomimicry: **procedural-with-bio-name**
- Evidence: `book_learner.py:812–830` — hot attractors and watch
  habits (questions + topics) have their narratives split on
  whitespace, filtered to len ≥ 4, and UNIONED into a single
  keyword set. This collapses 9 distinct WATCH_Q questions and 9
  distinct WATCH_T topics into one big bag. Then
  `_score_attractor_overlap` is a Jaccard on that bag. Result:
  a chunk about "language" scores the same overlap as a chunk
  about "psychology" as long as each hits 2-3 words. The watch
  structure has identity (questions are about reasoning moves,
  topics are about domains) but the scoring treats them as
  interchangeable tokens. The CP-affinity routing has the same
  problem (Gap 4 cross-ref). An honest version would keep each
  watch entry as its own probe and score chunk → watch_entry
  separately, then pick the strongest match.
- Proposed ticket:
  - id: T-watchlist-per-entry-scoring
  - title: watchlist — score chunks per watch entry, not on a union
  - size: S
  - tags: [reading, watchlist, biomimicry]
  - description: `_deposit_nodes` unions all watch habit keywords
    into one bag and scores chunk overlap against the bag. This
    loses the structure — a chunk about biology hits the bag same
    as a chunk about programming as long as the count matches.
    Shape of the fix: for each chunk, compute per-watch-entry
    overlap (`chunk_words ∩ watch_entry_words`), keep the
    top-K matches with their entry IDs in metadata
    (`matched_watches: [WATCH_T_06, WATCH_Q_02]`). This lets
    Igor answer "what have I learned about biology lately?"
    via an index on `metadata->'matched_watches' ? 'WATCH_T_06'`.
    NOT changed: the watch seeding, the overall gate policy
    (still no hard drop). Files:
    `lab/claudecode/book_learner.py`. Safe to ship
    independently. Pairs nicely with T-watchlist-actually-gate.
  - **Disposal: SHIP.**

---

## Dead-code cross-check

- Habits referencing non-existent code in your area: **none found**.
  `seed_reading_facia.py:66, 84` both point to
  `tools/reading_tool.py:reading` — exists. Archived
  `seed_foreground_reading_habits.py:51, 73` point to
  `tools.ebook_reader:start_foreground_reading` / `stop_foreground_reading`
  — exist at `ebook_reader.py:1598, 1667`. Good.
- Code in your area not referenced by any habit or test (orphan
  candidates):
  - `wild_igor/igor/tools/reading_benchmark.py` — registers no tool,
    no habit cites it, no test imports it. Used by CLI only for
    D360 7-pass benchmarking. Historically interesting but not
    live. Candidate for `archive/` or deletion.
  - `wild_igor/igor/tools/bootstrap_reader.py` — registers
    `start_reading_bootstrap` tool. grep shows only self-references
    + one test reference in `test_inference_gateway_mode.py`. The
    TWM mode primitive works (per the test) but no habit fires it
    and no live mention. Keep as a callable, but its
    "investment-in-quality" design intent has not been used in
    practice. Flag for Akien: is this still wanted?
  - `lab/tools/build_ebook_index.py` — referenced only from docs.
    Probably a prototype.
  - `wild_igor/igor/tools/reading_measure.py` —
    `reading_graph_baseline` tool registered but uncited. Partial
    implementation (only baseline, no "after"). Tied to Gap 1.
  - `lab/claudecode/reading_integrator.py` — invoked only via
    `reading_integration.py` subprocess shim. The subprocess shim
    is registered as a tool but I find no habit triggering it.
    Effectively dormant — Akien would need to call
    `integrate_reading` by hand. Tied to Gap 4.

---

## CC-workflow touchpoints in this area

- **Per-book progress file**: `PROGRESS_DIR / <md5-hash>.json` and
  `READING_<hash>.md` are local-filesystem artifacts that end up
  in `~/.TheIgors/book_learner_progress/`. Ticket opportunity: a
  pre-commit hook to refuse commits that drop runtime artifacts
  into the repo. Cross-refs `/validate-files`. Not specific to
  reading but exacerbated here.
- **Reading-as-sprint**: reading campaigns have much better budget
  accounting (`reading_campaigns.budget_usd`, per-item cost
  rollup) than sprint tickets do. Consider: could the ticket
  system adopt this shape? A named sprint with a budget envelope,
  auto-rollup of completed tickets by cost, a DEFER when budget
  exhausted. Not a finding, a prompt for Akien.
- **Skills that touch reading**: none currently. `/sprint`,
  `/commit`, `/savestate` are all generic. A `/read-campaign <name>`
  skill that wraps `reading_campaign.create_campaign +
  expand_campaign_from_master_list + worker_loop` would be a
  Haiku-appropriate mechanical skill — the work is pure
  orchestration. Flag as a tooling opportunity.
- **Haiku fit**: most reading operations (fetch, blob, run-status
  listing) are mechanical — good Haiku candidates. The
  extraction LLM call is already the expensive part and runs
  local-qwen, not through CC. CC involvement in reading is
  reviewing what Igor deposited, which is judgment work. Clear
  Haiku/Sonnet split: Haiku runs campaigns, Sonnet reviews
  deposits.

---

## What else?

- **What else should we be asking?** Is a book a unit, or a seed?
  The code treats a book as a fixed slab to be processed and
  deposited. A biological reader would re-surface old books at
  unpredictable intervals. There's no "I was reminded of
  Damasio's claim about somatic markers when Akien asked me X"
  mechanism — cross-book priming is absent despite the
  spreading_activation infrastructure existing (cross-ref
  persona 7 on priming). Gap-worthy: a T-reading-cross-book-
  priming ticket.
- **Cognition help**: the single highest-leverage cognitive
  change would be wiring `reading_list.encoding_arousal` into
  `cortex.search` ranking as a *retrieval* modifier. Currently
  it's deposit-time metadata with no query-time effect. If Akien
  said "this book is high-arousal at deposit", the nodes should
  preferentially surface — that's state-dependent memory in the
  biology. Bundling into T-reading-arousal-honest.
- **Small-hardware**: qwen-on-CPU is the real constraint. Two
  options: (a) tiny-model preparse (llama3.2:1b) that decides
  "is this chunk worth sending to qwen?" — a gate-before-gate
  that skips boilerplate. Cheap cost, real throughput win.
  Discussed in `reading_benchmark.py` as a quality benchmark
  but never wired as a gate. (b) batch the qwen calls: feed 3
  chunks per request using `/api/generate` streaming — Ollama
  supports batched prompts. File-worthy: T-reading-preparse-gate.
- **Engram audit for reading**: the `PROC_READING_*` family plus
  WATCH_Q / WATCH_T can be audited the way Pass 1 suggested for
  code. Key questions: (1) do the WATCH_Q questions actually
  fire on any chunks in the last month of deposits? if not,
  they're theatrical. (2) how many deposited FACTUAL nodes with
  `book_title` metadata have ever had their `activation_count`
  incremented? if < 10%, reading is a one-way sink. These are
  database queries, not code changes — an `/audit-reading`
  skill would be concrete.

---

## Summary

- Ticket candidates total: **13**
  (P1: 5 + Gaps: 8 = 13)
- Recommended SHIP: **6**
  - T-cloud-ok-override-fail-loud (P1.1)
  - T-reading-deposit-batched (P1.3) — highest leverage
  - T-reading-arousal-honest (P1.4) — highest biomimicry payoff
  - T-scan-ebooks-use-paths (P1.5)
  - T-reading-hang-safety (Gap 5)
  - T-drm-ghost-book-guard (Gap 9)
  - T-watchlist-per-entry-scoring (Gap 10) — small and clean
  (Counted as 7 above; tight count is 7 SHIP.)
- Recommended DEFER: **4**
  - T-reading-lab-wildigor-boundary (P1.2) — structural, big
  - T-reading-entry-points-canonicalize (Gap 4) — depends on
    the boundary fix
  - T-ebook-handle-cache-retire (Gap 6) — optimization
  - T-reading-state-consolidate (Gap 7) — schema move
  - T-replay-batch-edges (Gap 8) — low-priority perf
  (Counted: 5 DEFER.)
- Recommended INVESTIGATE: **3**
  - T-reading-densification-closed-loop (Gap 1)
  - T-watchlist-actually-gate (Gap 2)
  - T-calibre-8tier-arousal-or-retract (Gap 3)
- Recommended DISCARD: **0**. Nothing in this area was so
  specious it warranted retraction outright.

Adjusted totals: 7 SHIP, 5 DEFER, 3 INVESTIGATE, 0 DISCARD =
15 tickets (some Gap tickets split internally during writing).

- **Highest-stakes single finding**: T-reading-arousal-honest
  (P1.4). The `_arousal_from_cp` function is the single most
  load-bearing theatrical-biology instance in the reading area.
  Every deposited node for months has carried a fake arousal
  column that downstream code reads as real. Fixing it moves
  reading from theatrical to honest on the claim the subsystem
  is named for. The secondary pick would be Gap 1 (densification-
  closed-loop) — the whole subsystem's rationale rests on an
  unmeasured claim — but that's an INVESTIGATE, not a SHIP.

- **Biomimicry verdict on `_arousal_from_cp`**: **theatrical**.
  It is a CP-affinity keyword-hit score wearing the name "arousal".
  Arousal in the biology is a systemic state; in the code it's a
  per-chunk text relevance metric stamped permanently onto a row
  at deposit time, with no coupling to the actual milieu that
  models systemic arousal one module over. The honest version
  samples milieu state at encode time and modulates retrieval by
  current state. See ticket T-reading-arousal-honest.

- **One sentence for Pass 3**: Decide whether the reading
  subsystem's advertised claim ("reading densifies the graph,
  reducing cloud escalation") is worth the measurement work to
  prove it (Gap 1) — if yes, ship the instrumentation before
  shipping further reading features; if no, demote the claim in
  the docstring and reduce reading from "primary densification
  mechanism" to "another deposit path".
