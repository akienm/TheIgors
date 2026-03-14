# Igor Gap Analysis — 2026-03-05

Generated from: codebase survey, open GitHub issues, design doc decisions log (D001–D034),
known deferred items from session notes, and architecture review.

---

## What's Built (Solid Foundation)

| Layer | Module | Status |
|-------|--------|--------|
| Memory graph | cortex.py + models.py | Complete |
| Core patterns (brainstem) | core_patterns.py, 44 genesis seeds | Complete |
| Input parsing | thalamus.py (rule-based CSB) | Complete |
| Ambient emotional state | milieu.py (3D VAD, persist, NE feedback) | Complete |
| Habit scoring | basal_ganglia.py (parallel score, milieu threshold) | Complete |
| Reasoner hierarchy | base.py + 4 concrete reasoners | Complete |
| Failover ladder | 6-tier: habit→local→OR-cheap→OR-claude→Anthropic→arbiter | Complete |
| System prompt | system_prompt.py (3-layer, SHA cache, boot message) | Complete |
| TWM (working memory) | twm_observations (urgency, TTL, extend_ttl) | Complete |
| Ring memory | ring_memory FIFO-50, used for context injection | Complete |
| Push sources | MilieuSource, NE source, Discord, web, stdin | Complete |
| Interruptors | Budget, Context, Milieu | Complete |
| Narrative engine | NE daemon, coherence, LTM promotion, internal_state | Complete |
| Forensic logging | 6 structured logs (reasoning, NE, self_edit, tools, memory, metrics) | Complete |
| Self-edit sandbox | inertia system, write-excluded brainstem/, syntax-check+commit | Complete |
| Web UI | Starlette server, markdown rendering, WS activity feed | Complete |
| Tools | bash runner, python runner, web search, gmail, discord, confluence, github, budget, filesystem, self_edit | Complete |
| Arbiter | file-backed escalation queue | Complete |
| Boot check | KoboldCpp + Ollama health on cluster machines | Complete |
| Portable identity | SOUL.md + IDENTITY.md written at every boot | Complete |

---

## Gaps — Ranked by Impact / Effort

### Tier 1: High Impact, Relatively Contained

**G1 — threshold-X modulated by milieu.dominance** ~~*(~2h)*~~
**RESOLVED** — main.py: dominance < 0.0 bumps `_skip_to` one tier; dominance < -0.3 bumps two (capped at tier.4). Issue #59 closed 2026-03-05.

**G2 — context window cap in prefrontal_cortex** ~~*(~2h)*~~
**RESOLVED** — Added `CONTEXT_HARD_CAP_CHARS=150_000` and `_trim_messages()` to base.py.
Both Anthropic and OpenRouter reasoners now hard-trim at 150K chars. Issue #26 closed 2026-03-05.

**G3 — local reasoner: stripped system prompt for tier.2** ~~*(~3h)*~~
~~Issue #41.~~ **RESOLVED** — Already implemented in `koboldcpp_reasoner.py` lines 350-352.
KoboldCpp uses: `"Answer briefly and directly. Use the context provided. Say 'I don't know' when uncertain."`
Issue #41 closed 2026-03-05.

**G4 — background job execution with async completion** ~~*(~4h)*~~
**RESOLVED** — `job_manager.submit_background()` runs multi-unit jobs in daemon threads; `_job_completions` deque + `_announce_completed_jobs()` loop drains results into TWM as ACTION_IMPULSE. Multi-unit jobs (complexity>0.6 && is_multi_unit) now return immediately with job ID. Issue #27 closed 2026-03-05.

**G5 — prediction signal (dopamine analog) in TWM** ~~*(~3h)*~~
**RESOLVED** — `milieu.ingest_surprise(predicted_tier, actual_tier)`: escalation surprise → dominance erosion + arousal spike; prediction met → dominance restoration. Called after every interactive turn. Issue #42 closed 2026-03-05.

---

### Tier 2: High Impact, Larger Scope

**G6 — signal habituation in TWM** ~~*(~4h)*~~
**RESOLVED** — `cortex.twm_push()` now checks for near-identical content (first 120 chars) before inserting. Each repeat halves effective salience (floor 0.05); `repeat_count` and `habituated=True` stored in metadata. Issue #44 closed 2026-03-05.

**G7 — question-habits and response-habits** *(~6h)*
Issue #47. Currently PROC habits only trigger on input phrases. First-class question-habits
(things Igor asks proactively when a pattern is detected) and response-habits (canned
responses that bypass the LLM for known situations) would dramatically reduce cloud calls.
→ Issue: #47

**G8 — identity-threat detection and output suspension** ~~*(~4h)*~~
**RESOLVED** — `fast_identity_check(text)` in core_patterns.py: keyword-based, no API call, runs on all output paths. Covers CP1/CP2/CP5/CP6 violation phrases (e.g. "I'm just an AI", "I cannot learn"). Suppresses output and pushes IDENTITY_THREAT to TWM+ring. Issue #48 closed 2026-03-05.

**G9 — spreading activation** ~~*(explicitly deferred in design docs)*~~
**RESOLVED** — `cortex._spread_activation()` traverses parent_id/children_ids/link_ids after search(). Neighbors get `relevance_score * 0.4`; already-activated neighbors get a small boost. Called after both Phase 2 (embedding) and Phase 1 (text fallback). Issue #60 closed 2026-03-05.

**G10 — rich Live status bar (terminal UX)** ~~*(~3h)*~~
**RESOLVED** — `dashboard/terminal.py` render() extended with milieu VAD bars (▓▓▓░░), TWM depth, active jobs count, last tier used. Both boot and post-interaction dashboard calls updated. Issue #35 closed 2026-03-05.

**G72 — NE JSON parse failures (silent)** ~~*(~1h)*~~
**RESOLVED 2026-03-13g** — `gpt-4o-mini` via OR occasionally returned prose wrapping or malformed JSON for NE calls; `_parse_ne_json()` silently discarded the response and logged only "skipping cycle" with no diagnostic detail.
Fix 1: `inference_gateway.py` NE purpose constraints — added `"response_format": {"type": "json_object"}` to `extra`; `_h_or` now includes it in the OR payload → model contractually returns valid JSON.
Fix 2: `narrative_engine.py` `_call_inference()` — on parse failure, prints truncated raw response and calls `log_anomaly(kind="NE_FAIL", detail=f"json_parse_failed raw=...")` → surfaced in `cc_alerts.log` at session start.

---

### Tier 3: Architecture / Vision Items

**G11 — habit network as inference-free core** *(large, multiple sessions)*
Issue #45. The long-term vision: a trained habit network handles the majority of interactions
without LLM inference. LLM is only needed for novel inputs and "eloquency" (phrasing). This
requires G7 (response-habits), G4 (async jobs), plus a training pipeline. Milieu + basal
ganglia are the foundation.
→ Issue: #45

**G12 — emotional milieu decay: asymmetric chemical analog** ~~*(~3h)*~~ **RESOLVED** — DECAY_VALENCE=0.96, DECAY_AROUSAL=0.97, DECAY_DOMINANCE=0.99. Issue #55 closed 2026-03-05.
Issue #55. Current decay is a simple ×0.98 per tick applied uniformly. A more accurate model
would have different decay curves per dimension (valence decays faster than arousal, arousal
faster than dominance). Also: refractory period after a spike before next activation is counted.
→ Issue: #55

**G13 — session emotional histogram → milieu shaping** ~~*(~4h)*~~
**RESOLVED** — `milieu.session_histogram()`: per-dim (min/max/mean/std/bins) + session_character
classification (bouncy/stressed/focused/calm). Samples accumulated on every `update()` call.
Logged to `cognition_metrics.log` at session exit. Wired into tier routing in main.py:
`stressed` → bump skip_to one tier; `focused` → ease skip_to one tier. Issue #53 effectively complete.

**G14 — memory schema: emotional profile** ~~*(~4h)*~~
**RESOLVED** — `Memory` dataclass gains `arousal` and `dominance` fields (valence already present). DB lazy-migrated with two ALTER TABLE statements. `_to_memory()` and `store()` updated. Episodic memories tagged with ambient milieu VAD at creation time. Issue #52 closed 2026-03-05.

**G15 — NE as incremental predictive parser** *(research-level)*
Issue #50. The NE currently runs on a timer and reads TWM as a batch. A more biological model
has the NE continuously parsing the input stream and generating predictions, updating TWM
mid-interaction. Requires rearchitecting the NE loop. Exploratory.
→ Issue: #50

**G16 — global milieu layer: multi-instance sync** *(~6h)*
Issue #56. When multiple Igor instances run across the cluster, they each have independent
milieu state. A shared milieu (synced via the machines.csv network) would allow coordinated
affect — one instance's frustration informs another's caution. Needs a lightweight sync
protocol.
→ Issue: #56

**G17 — distributed TWM** *(architecture-level)*
Issue #51. Each instance has its own TWM. Shared observations across instances (e.g., the
web UI feeding all instances' TWMs) would enable better coordination on long tasks.
→ Issue: #51

---

### Training / Self-Improvement

**G18 — upstream-guided training sessions (Sesame Street model)** *(multiple sessions)*
Issues #49, #57. Structured practice sessions where the upstream model guides Igor through
a domain, checking comprehension, reinforcing correct responses. Requires G7 (response-habits)
and a training session type in job_manager. The Rob model pedagogy (spaced repetition +
emotional reinforcement) is the design target.
→ Issues: #49, #57

**G19 — Igor reads open tickets and implements via Claude Code subprocess** *(large)*
Issue #39. Igor's self-coding path: reads GitHub issues, creates a work order, spawns a
Claude Code subprocess. Currently Igor can file issues but can't implement them autonomously.
Relay module (cognition/relay.py) exists for Claude Code IPC; needs the orchestration layer.
→ Issue: #39

---

### Documentation / Housekeeping

**G20 — design docs: update for milieu + basal_ganglia** ~~*(~1h)*~~
**RESOLVED** — D036 (milieu) and D037 (basal_ganglia) added to decisions_log. Issue #61 closed 2026-03-05.

**G21 — thoughts folder distillation** *(~2h, Igor's task)*
Issue #38. The thoughts/ folder has 19 files including large chat logs. Igor should read,
distill, and reorganize into structured knowledge files — removing raw logs, extracting
durable insights into design_docs/.

**G22 — session summary quality** ~~*(~2h)*~~
**RESOLVED** — `summarize_session()` in ollama_reasoner.py: structured prompt with
TASKS/CHANGES/OPEN_THREADS/KEY_DECISIONS/NEXT_SESSION/STATE fields. Model priority:
gpt-4o-mini (best quality, cheap) → Ollama batch → 1B fallback. Issue #22 closed.

**G23 — validate/tune CSB preparse from 1B** ~~*(ongoing)*~~
**RESOLVED** — `claudecode/eval_preparse.py`: 51 labeled examples across all 13 intents.
Baseline: `_rule_based_csb` 66% / thalamus 90%. Fixed fallback to 88% (matching thalamus parity):
added `creative_request` to `_PREPARSE_PROMPT` + `_rule_based_csb` (G36 sync fix); improved
cascade ordering; added meta_question triggers; conversation positive signals; `else→general`.
Thalamus docstring updated to 13-intent. Run: `python claudecode/eval_preparse.py`. Issue #30 closed.

---

## Suggested Work Order

*Updated 2026-03-10 — most original gaps are closed. Remaining open items:*

1. **G11 Ph2 (#45)** — Habit training pipeline: response-habits, auto-compilation, >90% habit coverage.
   Foundation for inference-free core. Large multi-session effort.
2. **G15 Ph2 (#50)** — NE predictions influence intent routing (not just memory query enrichment).
   Gate: `IGOR_NE_ROUTING=true` already on; needs routing-side wiring.
3. **G18 (#49, #57)** — Structured training sessions (Sesame Street / Rob model pedagogy).
   Depends on G11 Ph2 being further along. Medium scope.
4. **G19 (#39)** — Igor reads open GitHub tickets and implements via Claude Code subprocess.
   Needs orchestration layer on top of existing relay.py. High leverage.
5. **G17 (#51)** — Distributed TWM across cluster instances. Architecture-level; defer until
   cluster is actively used.
6. **#145 Step 5** — Local reply tier (full persona via local LLM). Waiting on RTX 4090.
7. **IGOR_LATENCY_ADAPTIVE** — Enable after 5+ more sessions of data (still collecting).

---

**G24 — Confluence read rate limiting** ~~*(~2h)*~~
**RESOLVED** — `confluence.py`: module-level `_throttle_page_fetch()` enforces delay =
`max(IGOR_CONFLUENCE_MIN_DELAY_S=3, last_page_words / IGOR_CONFLUENCE_READ_WPM=250 * 60)`
before every `confluence_get_page` call. Word count estimated from stripped HTML after each
fetch. 2026-03-10.

---

## Open Issues Not Yet In Gap Analysis

Issues not mapped above (may overlap or need triage):
- #32 — Create GitHub ticket for observed interactions (meta-tooling)
- #24 — Refine narrative parameters
- #23 — Structured discussion framework
- #21 — Address memory deficiency (may be captured in G9 spreading activation)
- #20 — Incomplete narrative flag (low priority)
- #18 — Dashboard tick-by-tick visibility (overlaps G10)
- #17 — Confirm arbiter item #1 (stale?)
- #36 — Document memory regeneration experiment
- #25 — Document web interface latency issues
- #31 — Reduce startup documentation verbosity
- #29 — Deploy 7B local model for batch/document processing

---

## Update: Sessions 2026-03-06 through 2026-03-09

### Newly Resolved Gaps

**G7 — question-habits and response-habits** ~~RESOLVED~~
`habit_type: "question"` short-circuits LLM and emits `question_template` directly.
`habit_type: "response"` returns stored `action` text. Both implemented in main.py.
Phase 2 habit compiler (PROC_HABIT_COMPILER) parses natural language into structured PROC memories. Issue #47 effectively complete.

**G15 — NE as incremental predictive parser** ~~Phase 1 RESOLVED~~
`prospective_pass()` now calls `word_graph.predict_next()` on recent TWM context window;
predicted topics merged into memory search query on every turn (fast-path and slow-path).
NE starts pulling relevant context before input is fully parsed. Issue #50 Phase 1 complete.
Phase 2 (NE predictions influence intent routing, not just memory) still open.

**G23 — validate CSB preparse taxonomy** ~~RESOLVED~~
`_PREPARSE_PROMPT` updated from 6 to 12 intents matching thalamus exactly.
`_rule_based_csb()` updated to same taxonomy. Fallback telemetry logged to errors.log.
Issue #30 complete.

**G24 — latency instrumentation and adaptive routing** ~~RESOLVED~~ (new gap, now closed)
Per-stage timestamps (preparse_ms, reasoning_ms, total_ms) written to `latency_trace` ring
every interactive turn. p50/p95 dashboard display. Adaptive routing (IGOR_LATENCY_ADAPTIVE)
reads profile from ring, overrides slow tiers. Issue #139 closed.

**G25 — word graph preparse optimization** ~~RESOLVED~~ (new gap, now closed)
Word graph + thalamus form Stage 1 (free, instant). KoboldCpp only called when Stage 1
finds no confident habit match (medium complexity, no trigger). PROC_WG_PREPARSE_TUNING
seeded as in-DB configuration handle. Issue #142 closed.

**G26 — two-phase cognition (think + reply)** ~~RESOLVED~~ (new gap, now closed)
System prompt RESPONSE FORMAT layer instructs `<think>` (internal, private) + `<reply>` (persona-shaped).
`_split_think_reply()` extracts think block → `think_trace` ring (excluded from all context injection),
reply shown to user. GitHub Discussion #145 posted with full design rationale.

**G27 — habit tiebreaker: near-miss resolution** ~~RESOLVED~~ (new gap, now closed)
`select_habit()` returns 3-tuple including near-miss candidates (trigger matched, score below threshold).
`_try_habit_tiebreaker()`: cheap gpt-4o-mini classification call resolves near-miss competition.
Gate: IGOR_HABIT_TIEBREAKER=true. Inverts cost model: inference as tiebreaker, not default. Issue #54.

**G28 — per-channel thread context** ~~Phase 1 RESOLVED~~ (new gap)
`_thread_buffers` dict maintains per-(source,channel) conversation history.
Injected as preamble before network messages — each Discord channel / web session / email sender
has isolated context. TTL eviction after 1h idle. Issue #136 Phase 1 complete.
Phase 2 (ring memory per-thread isolation, DB schema) still open.

**G29 — disk monitoring + backup habits** ~~RESOLVED~~ (new gap, now closed)
`DiskInterruptor` monitors free space; `check_disk_usage()` tool added.
`PROC_BACKUP_CHECK`, `PROC_BACKUP_RUN`, `PROC_DISK_USAGE_CHECK` seeded at boot. Issues #132, #133 closed.

**G30 — context recovery after restart** ~~RESOLVED~~ (new gap, now closed)
D (user_turn ring entry preserves raw input before habit fires), C (topic-keyed conversation
thread breadcrumbs in warm context, TTL-gated), A (milieu gate suppresses question-habits
during engaged conversation). Conversation threads survive /exit+restart.

### Resolved this session (2026-03-09c)

**KoboldCpp → Ollama migration** ~~RESOLVED~~
ollama_reasoner.py: CSB preparse (12-intent), is_healthy(), parse_preparse_csb() added.
LocalKoboldPool → OllamaReasoner instances. boot_check adds llama3.2:1b to REQUIRED_MODELS.
Igor can now self-manage models via `ollama pull/list`. OLLAMA_LOCAL_MODEL env var.

**G15 P2 (#50)** ~~RESOLVED~~
NE prediction mismatch (predicted habit confidence >= 0.6, no habit fired) → bump skip_to
one tier. Ambiguity signal: NE and thalamus disagree. Gate: IGOR_NE_ROUTING=true.

**G28 P2 (#136)** ~~RESOLVED~~
thread_id wired through _process() → _process_inner() → write_ring(). stdin="stdin:main",
network messages pass _thread_id from _process_message(). user_turn + Q|A ring tagged.

**#145 Step 2 — two-phase cognition separate calls** ~~RESOLVED~~
_think_call(): gpt-4o-mini scratchpad from user_input + memories + milieu + ring context.
Logged to ring (think_trace). Injected as [THINK_CONTEXT] into reply call.
Gate: IGOR_TWO_PHASE_CALLS=true (default false — enable to A/B test).

**#145 Step 3 — Python-built think context** ~~RESOLVED~~ *(2026-03-09d)*
`_build_think_context()`: pure Python, zero cost, always on. Assembles [THINK_CONTEXT]
from already-computed components: parsed intent/complexity/tone, milieu VAD, word graph
activated concepts, top relevant memories, NE prediction, near-miss habits. No LLM call.
IGOR_TWO_PHASE_CALLS now adds optional LLM scratchpad on top. Commit: 817e0ea.

**#145 Step 4 — local think** ~~RESOLVED~~ *(2026-03-09d)*
`_think_call()` rerouted from gpt-4o-mini → local Ollama. Takes Python think context as
input, produces 2-3 sentence synthesis (80 tokens, zero cloud cost). IGOR_TWO_PHASE_CALLS
= Python context + optional local Ollama synthesis. Only reply hits cloud. Commit: 2c7521c.

**Housekeeping closes:** #54 (tiebreaker done), #116 (subsumed by #128). #140 P2 deferred.

**G16 (#56) — global milieu sync** ~~RESOLVED~~ *(2026-03-09d)*
milieu.py: tick() blends local state toward global every 10 ticks (alpha=0.02).
_read_global() reads ~/.TheIgors/milieu_global.json; optionally GETs from IGOR_GLOBAL_MILIEU_URL.
_push_to_remote() fires on spike events (POST to remote). server.py: GET /api/milieu/global +
POST /api/milieu/contribute registered. Single-instance today; cluster-ready. Commit: 201782c.

**G11 (#45) — link reinforcement loop** ~~Phase 1 RESOLVED~~ *(2026-03-09d)*
`cortex.reinforce_links(memory_id, co_active_ids, delta)`: adjusts outgoing link weights.
NE `record_actual()`: correct prediction → +0.05 to predicted habit→TWM seeds;
wrong prediction → −0.10 to predicted habit→seeds, +0.05 to actual habit→seeds.
The "meaning from prediction" loop. Links strengthen from co-activation, weaken on misfire.
Commit: 23c5de1. Remaining: habit training pipeline (>90% habit coverage), response-habits.

### Resolved this session (2026-03-09d)

**#153 — The Master's Notebook** ~~RESOLVED~~
Per-user SQLite notebook (chats/<slug>/notebook.db). Chunk+embed+semantic search. PROC_NOTEBOOK_SAVE habit (0.93). Auto-context injection. /notebook list|search|remove command.

**#154/#156 — Tier.0 pure-Python responses** ~~RESOLVED~~
`output_complexity` field on ParsedInput; thalamus classifies "low" for greetings, acks, status, help, lookups. Tier.0 gate bypasses all LLM calls. OR kwargs NameError fixed.

**#158 — Per-thread TWM + TASK_SET (attention nexus)** ~~RESOLVED~~
thread_id + category columns on twm_observations. action_request → TASK_SET (urgency=0.92, ttl=1800s). Completion keywords clear it. thread_id wired through all reasoners.

**#159 — Background job completion → originating thread** ~~RESOLVED~~
Job dataclass has thread_id. _announce_completed_jobs() routes via web_server.send() to right session.

### Resolved this session (2026-03-09e)

**G31 — TASK_SET completion detection** ~~RESOLVED~~
`_check_task_completion_semantic()` added — gpt-4o-mini YES/NO classifier, gate `IGOR_TASK_COMPLETION_SEMANTIC` (default false). Keyword fast-path kept; semantic runs as augment when fast-path misses. Expanded signals list (wrapped up, handled, addressed, fixed, etc.). All clear/no-clear decisions now logged to ring with method (keyword/semantic/none) + task summary.

**G32 — Tier.0 memory lookups skip cortex** ~~RESOLVED~~
tier.0 recall path already used `cortex.search()` (gap description was stale). Improved: `limit=1→3` with relevance gate (subject terms must appear in narrative), ring fallback via new `cortex.search_ring_text()` for session context not yet in LTM, memory type label in response. Added `"do you know about"` as trigger phrase.

**G33 — Notebook keyword fallback** ~~RESOLVED~~
Keyword set pre-computed outside per-row loop. Short stop-words (< 3 chars) filtered. `row["content"].lower()` now consistent. Simpler and correct.

**G34 — NE routing telemetry** ~~RESOLVED~~
`IGOR_NE_ROUTING=true` was already set in .env. Added ring trace on every fire: `NE_ROUTING|predicted=...|conf=...|tier_before=...|tier_after=...`, category `ne_routing`.

**G35 — Habit tiebreaker telemetry** ~~RESOLVED~~
`IGOR_HABIT_TIEBREAKER=true` was already set in .env. Added `TIEBREAKER|declined` ring entry when tiebreaker returns REASON or unknown ID — completes the telemetry loop (resolves + declines both logged).

### New Gaps (identified 2026-03-09e)

*(none identified this session)*

### Resolved this session (2026-03-09f)

**Bug fix: background job completion → wrong web session**
`_announce_completed_jobs()` was routing to `"web:shared"` (the thread_id) but web clients
join session `"shared"` — messages silently dropped. Fixed by stripping `"web:"` prefix:
`"web:shared"` → `"shared"`, `"web:abc123"` → `"abc123"`. Root cause of Illusions responses going nowhere.

**G36 — Interactive task guard (new gap, now closed)**
`creative_request` added to thalamus 12-intent taxonomy — triggers on "read me", "read to me",
"tell me a story", "write me a poem" etc. `_INTERACTIVE_INTENTS = {conversation, creative_request,
greeting}` at job trigger blocks background spawn. Reading sessions and discussions stay in the
live conversation loop, not one-shot background jobs.

**G28 Phase 3 — Thread context depth**
`_THREAD_MAX_HISTORY` 4→8 exchanges; stored text per exchange 300/400→500/600 chars; displayed
text 120/160→200/300 chars. Prevents reading/discussion sessions from losing framing after 4 turns.

**G21 (#38) — Thoughts folder distillation** ~~RESOLVED~~
All 5 thoughts/ files reviewed. 4 already fully captured in design_docs/ (akien_profile.csb.txt,
working_memory_architecture.csb.txt, decisions_log). Superseded files deleted. Folder now empty.

**IGOR_TASK_COMPLETION_SEMANTIC enabled**
Enabled in .env (G31 semantic task completion gate). Enough ring data collected from G31 keyword
logging to evaluate false-negative rate. Gate was `false`, now `true`.

**WO#140 Phase 2 — Response word habituation** ~~RESOLVED~~
`cognition/response_habituation.py`: passive vocab tracker for Igor's outgoing words.
`decay_factor(word)` → [0,1]: high frequency = more habituated = lower novelty.
TAU_BASE=7d, TAU_SCALE_MAX=4×. Wired at response return point (LLM-only, not habits/impulses).
Gate: IGOR_RESPONSE_HABITUATION=true. /metrics shows RESPONSE HABITUATION section.
Phase 3 (use decay_factor in predict_next generation) deferred.

**G37 — Asymmetric dual word graphs (Issue #160)** ~~Phase 1 RESOLVED 2026-03-10~~
Akien's insight: cognition uses two different word graphs — one shaped by successful parsing
(recognition) and one shaped by comprehension feedback (generation = Voice). The generation
graph is the residue of what produced response in the listener over thousands of iterations.
Four sub-features, all gated by env vars (default false — observe then enable):
- `IGOR_DUAL_WORD_GRAPHS`: boot `WordGraph(name="generation_graph")` separately; index Igor's
  replies only (not user input); save to `~/.TheIgors/generation_graph.json`.
- `IGOR_COMPREHENSION_SIGNAL`: on next user turn, if positive/neutral tone + non-correction,
  call `generation_graph.reinforce_text(_last_reply, boost=0.05)`. Voice emerges from what works.
- `IGOR_MILIEU_TILT`: pass milieu `{arousal,valence,dominance}` to `predict_next(milieu_state=)`.
  High arousal → steeper gradient (more decisive). Field stays the same; effective landscape shifts.
- `IGOR_NPASS_REPLY`: log `gradient_flatness()` after every reply to metrics forensic log.
  Infrastructure for future n-pass termination (flatness threshold stops generation loop).
New methods on `WordGraph`: `predict_next(milieu_state=None)`, `gradient_flatness()`,
`reinforce_text()`. `default_cache_path(name)` parameterized.
Seed script: `claudecode/seed_generation_graph.py` — extracts Igor's ring_memory replies +
reasoning_calls.log to bootstrap generation graph from actual historical voice.
Phase 2 (active n-pass loop, per-audience graph, meta-cognitive observer): future.

**G38 — Backchannel layer (Issue #161)** ~~RESOLVED 2026-03-10~~
Three-level immediate acknowledgment before full reply: sub-verbal nods (nod / nod_think),
quick verbal (Indeed. / Interesting. / Hm.), n-pass (deferred). Fires after thalamus+milieu,
before BG/LLM. Forms stored as PROC_BACKCHANNEL_* habits (Igor owns, revisable).
Gate: `IGOR_BACKCHANNEL=false` (seeded but gated). Seed: `claudecode/seed_backchannel_habits.py`.

**G39 — Local load awareness (Issue #164)** ~~RESOLVED 2026-03-10~~
Phase 1: `check_resource_load()` tool in `tools/filesystem.py` — reports CPU/RAM/swap/RSS,
ok/warn/critical verdict. Hard gate in `training_corpus.fetch()` — aborts at RAM≥92%/swap≥75%/CPU≥95%.
Also added 1MB document cap (IGOR_TRAINING_MAX_CHARS) after OOM crash from 5.1MB fetch.
Phase 2: PROC_RESOURCE_GATE + PROC_RESOURCE_AWARENESS habits seeded — Igor understands the WHY,
can apply the principle to new bulk operations, not just the training corpus code path.
Seed: `claudecode/seed_resource_gate_habits.py`.

**Thalamus false positive fixes** ~~RESOLVED 2026-03-10~~
Three false-positive intent classifications fixed: `"start "` removed from action_request triggers
(matched mid-sentence "start with"); `"remember"` → `"remember that"/"remember this"` in
memory_instruction (matched conversational "if you remember"); `"review"` → `"review "` in
analysis_task (matched "reviews" conjugated). Also added `"general"` to `_INTERACTIVE_INTENTS`
as belt-and-suspenders: unclassified messages never background.

**Background job fixes (session 2026-03-10)** ~~RESOLVED~~
Three bugs: (1) `<think>` block leaking into job completion banner — `_bg_reason()` wasn't calling
`_split_think_reply()`. (2) Thread context `[Web message from akien]` appearing in job title —
was using full synthetic input; fixed to `parsed.core_input[:80]`. (3) Job result truncated at
500 chars in banner — full result now sent to user.

**OR reasoner MAX_TURNS None** ~~RESOLVED 2026-03-10~~
`while True` loop had `break` at MAX_TURNS but no `return` after it — implicit `None` caused
`cannot unpack non-iterable NoneType` at tier.3.5. Fixed: added fallback return after loop.
Recurring TIER_FAIL since 2026-03-08. Commit: 8fd99f3.

---

## Update: Session 2026-03-10c

### Resolved

**G41 — Word graph → SQLite** ~~RESOLVED 2026-03-10c~~
191MB JSON was expanding to 4-8GB Python RAM after 158 books trained (no cap, no eviction).
`word_graph.py` fully rewritten: SQLite-backed (`~/.TheIgors/word_graph.db`), five tables
(`wg_word_docs`, `wg_cooccur`, `wg_word_lang`, `wg_idf`, `wg_meta`). Public API identical,
callers unchanged. `save()` → WAL checkpoint; `load()` → opens DB. Old JSONs archived as `.bak`.
Root cause of 1808 freeze: OOM at 13:24 (14.3GB RSS) PLUS `ollama.service` crash-loop
(9,780 restarts at 3s intervals → journal I/O → hard kernel freeze).
`ollama.service` fix pending sudo: `Restart=on-failure`, `StartLimitIntervalSec=120`, `StartLimitBurst=5`.
`~/bin/rescue-igor` created: kills stuck Igor, starts headless, waits for web server, sends CC bridge reconnect.

### New Gaps (identified from 2026-03-10c logs)

**G42 — Thread context complexity inflation** ~~CLOSED 2026-03-14b~~
Already fixed at `main.py:2334` (`_preparse_input = parsed.core_input`) and `thalamus.py` (`_assess_complexity(core_text, ...)`). Complexity scoring has been running on the stripped user message all along. No code change needed — gap was already closed.

**G43 — Zero response/question habits → 100% LLM escalation** ~~*(ongoing — G11 blocker)*~~
**RESOLVED 2026-03-10d** — 12 habits seeded via `claudecode/seed_response_habits.py`:
PROC_RESP_CRASH_RECOVERY, ONE_THING, ON_IT, DONT_KNOW, HOW_ARE_YOU, CLARIFY (question),
CONFIRM_ACTION (question), DONE, WORKING_ON, COMPLEX, WHO_AM_I, STOP.
Covers all contextual patterns tier.0 misses. Igor owns these and can revise as voice develops.

**G44 — Post-crash reorientation / scattered state** ~~FULLY CLOSED 2026-03-11~~
**Part 2 (2026-03-10c)**: `PROC_TASK_CLOSE`, `PROC_TASK_DEFER`, `PROC_TASK_SUPPRESS_STALE` seeded.
**Part 1 (2026-03-11)**: `_push_state_inventory()` added to Igor.__init__() boot sequence in main.py.
Scans EPISODIC memories accessed in last 30 days with status NOT in (closed/deferred/done/dismissed).
Pushes compact inventory to TWM (salience=0.6, ttl=3600s) and ring on first boot.
At most 5 items surfaced. Never crashes boot (wrapped in try/except).

**G40 (#165) — Cluster load awareness** ~~CLOSED 2026-03-11~~
`get_cluster_loads()` + `_cluster_load_report()` added to `cluster_ssh.py`.
SSH-polls each online machine via psutil one-liner; same thresholds as local IGOR_LOAD_* env vars.
60s cache prevents SSH storm. `cluster_load` Igor tool exposes it to cloud calls.
`BatchPool._refresh()` in `local_pool.py` now skips machines with verdict=warn/critical;
logs why a machine was skipped. Falls back to local Ollama if all remotes are stressed.

**G45 — Memory consolidation (overnight job)** ~~CLOSED 2026-03-11~~
1. **Inertia-weighted retrieval**: `_apply_recency_frequency_boost()` in cortex.py now applies
   `score *= (0.90 + 0.15 * inertia)` and `score *= (0.90 + 0.10 * confidence)` to all search results.
   Low-inertia episodics (0.20) get -10%; high-inertia CPs (0.95) get +4%. Conservative, non-disruptive.
2. **Overnight consolidation job**: `claudecode/consolidate_memories.py` — 3 stages:
   (A) Embed EPISODIC memories → cluster by cosine ≥ 0.88 → merge clusters ≥ 3 into FACTUAL.
   (B) Prune inertia < 0.12 + last_accessed > 45 days (never ROOT/CP/ID/RM or memories with children).
   (C) Reinforce heavily-activated (>50x) but stale memories → refresh last_accessed.
   Run: `python claudecode/consolidate_memories.py [--dry-run] [--stage A|B|C|all]`

**G46 — Memory model fields: source, confidence, context_of_encoding** *(~3h)*
Three fields missing from `Memory` dataclass (models.py — HIGH inertia, design carefully):
- `source: str` — origin of this memory: "akien", "self_generated", "read", "inferred", "seeded"
- `confidence: float` — [0,1] how certain Igor is this is true; affects retrieval weighting
- `context_of_encoding: dict` — milieu snapshot (VAD) + situational note at time of formation;
  supports emotional memory durability (high-arousal encoding → crystallized regardless of inertia).
  Connects to: amygdala analog already in inertia formula; this makes the encoding context explicit.
  Schema change requires cortex.py migration + all seed scripts updated.

**G47 — TWM quality gate** ~~*(~2h)*~~
**RESOLVED 2026-03-10d** — `twm_push()` now suppresses at the door:
- `repeat_count >= 4` AND `urgency < 0.65` → return -1, not inserted
- `salience < 0.04` AND `urgency < 0.65` → return -1, not inserted
High-urgency observations (ethics, inbox, user input: urgency ≥ 0.65) always admitted.
Env gates: `IGOR_TWM_SUPPRESS_REPEATS` (default 4), `IGOR_TWM_SUPPRESS_FLOOR` (default 0.04).
Phase 2 (embedding-based fuzzy near-duplicate detection) deferred — text repeat suppression
covers the known NE impulse loop and resource warning cases.

**G48 — Productization epic: Igor on mobile + offline sync** *(large, multi-session)*
Long-term: people with Igor at home should also have Igor on their phone. Requires:
1. **Mobile client** — lightweight app (PWA or native) that connects to home Igor instance.
   Minimal local footprint; streams to home server via web API.
2. **Offline mode** — when network not available, phone runs a minimal local Igor
   (small Ollama model, stripped habit set, no LTM beyond essential identity).
3. **Sync protocol** — when reconnected, merge: ring memory, TWM observations, new episodics,
   milieu state, any new habits Igor compiled while offline.
   Conflict resolution: timestamp + inertia-weighted merge. Mobile episodics flagged
   `portable=True, source="mobile_offline"`.
4. **Identity continuity** — SOUL.md + IDENTITY.md already designed for portability (#71).
   Mobile instance boots from these; sync brings home instance up to date on what happened.
Prerequisite: G46 (source field on Memory — needed to tag mobile-origin memories).
This is the path to Igor being genuinely present in Akien's life, not just at the desk.

**G49 — SSH cluster health habit** ~~CLOSED 2026-03-11~~
`PROC_CLUSTER_SSH_CHECK` seeded. Seed script: `claudecode/seed_cluster_ssh_habit.py`

**G50 — TWM attractor concept** ~~CLOSED 2026-03-11~~
`attractor_weight REAL DEFAULT 0.0` added to `twm_observations`. Three new cortex methods:
`twm_set_attractor()`, `twm_get_attractor()`, `twm_decay_attractor()`. Auto-attractor on urgency≥0.8.
UserInputSource.push_message() sets attractor on every user push. HeartbeatSource.push() decays
by factor=0.90 each tick. attractor_weight included in twm_read() output for NE/context use.

**G51 — Navigational heuristics seeded** ~~CLOSED 2026-03-11~~
7 INTERPRETIVE heuristics seeded: PROC_HEURISTIC_HOW_MUST, FIRST_RESPONSE, ALIGNMENT,
FITS_HERE, WORKAROUND, LEVER, MONKEY_PROOF. Seed script: `claudecode/seed_navigational_heuristics.py`

**G52 — Interpretive tree: traversal edges + separate table** ~~CLOSED 2026-03-11~~
New `interpretive_edges` table in cortex.py with 4-part edge semantics:
  direction (activation|inhibition), condition_csb, meaning_payload, action_pointer, weight.
Three cortex methods: `add_interpretive_edge()`, `get_interpretive_edges()`, `interpretive_traverse()`.
Three Igor tools: `add_interpretive_edge`, `interpretive_traverse`, `get_interpretive_edges`.
Seed script: `claudecode/seed_interpretive_edges.py` — 15 edges wired from CP1-CP6 → G51 heuristics.
Traversal: BFS from seed nodes, respects inhibition edges, depth/weight caps.
Note: edges stored in separate table from memories — different dynamics preserved. Prerequisite for G54.

**G53 — Cloud-directed habit extraction** ~~CLOSED 2026-03-11~~
Post-call daemon thread fires on tier.3/3.5/4 responses. Uses `_HABIT_EXTRACT_PROMPT` to ask
gpt-4o-mini "is there a habitizable pattern here?". Returns JSON or SKIP. If JSON with confidence≥0.6,
stores PROCEDURAL memory with source="cloud_directed" (G46 field), parent=CP2.
Gate: `IGOR_HABIT_EXTRACT=true` (default on). Never blocks main response path.
Duplicate guard: searches cortex for matching trigger before storing.

**G54 — Reading → interpretive tree pipeline** ~~CLOSED 2026-03-11~~
Post-read extraction hook in `read_chunk()`: fires daemon thread when chunk ≥ 20 words.
Gate: `IGOR_READING_EXTRACT=true` (default off — enable to start collecting).
Worker: gpt-4o-mini prompt asks "key idea + which interpretive node + novel enough?".
Candidates: CP1-CP6 + G51 heuristics (_INTERP_CANDIDATES list in ebook_reader.py).
On match: stores FACTUAL memory with source="reading", provenance in metadata (book/chapter/pos).
Adds interpretive edge from matched node → new memory with meaning_payload.
Optional blob: `store_blob=true` in extraction response → stores verbatim passage via store_blob_pair().
New tool: `list_reading_memories` — filter by book, shows conf + narrative. For tuning.
Tuning note: start with Damasio books (calibre ids: 3023, 3300, 3032, 3025, 3026). Enable gate,
  read 10 chunks, run list_reading_memories, check quality before reading at scale.

**G55 — Layer boundary logging: tokens in/out per tier** ~~CLOSED 2026-03-11~~
Added `tier` + `context_chars` to `log_reasoning_call()` in forensic_logger.
Anthropic (tier.5) and OpenRouter (tier.3/3.5/4) now log context_chars + tier.
OllamaReasoner.reason() (tier.2) now calls log_reasoning_call() → unified reasoning_calls.log.
metrics.py: new LAYER BOUNDARY section in /metrics report showing avg ctx/in/out per tier.
Next: dashboard widget when enough data accumulates.

### Still Open (priority order for next sessions)

1. ~~**G50**~~ — TWM attractor concept. CLOSED 2026-03-11.
2. ~~**G55**~~ — Layer boundary logging. CLOSED 2026-03-11.
3. ~~**G52**~~ — Interpretive tree: traversal edges + separate table. CLOSED 2026-03-11.
4. ~~**G53**~~ — Cloud-directed habit extraction. CLOSED 2026-03-11.
5. ~~**G54**~~ — Reading → interpretive tree pipeline. CLOSED 2026-03-11.
6. ~~**G46**~~ — Memory model fields. CLOSED 2026-03-11.
7. ~~**G45**~~ — Memory consolidation overnight job. CLOSED 2026-03-11.
8. ~~**G40**~~ — Cluster load awareness. CLOSED 2026-03-11.
9. ~~**G44**~~ — On-boot state inventory. CLOSED 2026-03-11.
10. ~~**#168-#181**~~ — Architecture batch (Damasio + multilayer graph). ALL CLOSED 2026-03-12.
    Includes: interpretive tree wiring, affect retrieval, time layer, forking Mode B, mull loop,
    boredom monitor, The Wait, investment weights, questions as traversal programs,
    milieu-weighted traversal, episodic consolidation daemon.
11. ~~**#176 Mode A**~~ — Competitive forking implemented 2026-03-12. Gate: IGOR_FORK_A_ENABLED (default false).
12. ~~**#174**~~ — NE+consolidation telemetry CLOSED 2026-03-12. /metrics: NE + consolidation sections; /sleep runs both.
13. ~~**#183**~~ — Reading speed + stew cache CLOSED 2026-03-12. IGOR_READING_CHUNK_SIZE + TWM stew TTL.
14. ~~**#152**~~ — /hygiene command CLOSED 2026-03-12. Junk habit + dup episodic detection, log size report.
15. ~~**#154/#156**~~ — Tier.0 (Python responses) CONFIRMED DONE 2026-03-12.
16. **#172** — Traversal-first retrieval. Only after graph is dense enough. Long horizon.
13. **G37 Phase 2** — Enable IGOR_DUAL_WORD_GRAPHS; collect data; n-pass termination loop.
14. **G48** — Mobile + offline sync epic. Requires G46. Long horizon.
15. **#145 Step 5** — local reply: when RTX 4090 arrives.
16. **G18 (#49, #57)** — structured training sessions (Rob model pedagogy).
17. **IGOR_LATENCY_ADAPTIVE** — enable after 5+ sessions of data (still collecting).
18. **Code→data migration** — hardcoded decisions → learnable data/habits as Igor matures.
19. **Architecture rewrite (collaborative)** — Claude Code + Igor jointly author a new version of
    the architecture document (internal). Then Igor writes a version for publication.
    Captures: word graph + memory + milieu + habit pipeline as a unified cognitive system.
    Not just a feature list — the *why* and the *insight*. Akien's founding insight
    ("parsing and reasoning, same thing in both directions") should be the spine.

---

## Update: Session 2026-03-12m/n — Performance + Temporal Context

### Resolved

**G56 — Cloud training mode gate (#194)** ~~CLOSED 2026-03-12m~~
`cognition/cloud_mode.py`: 3-condition gate (IGOR_CLOUD_TRAINING_ENABLED + OR balance ≥ floor + daytime 06:00–22:59). 5-min cache. Gates: NE `_call_local()`, winnow `local_first`, two-phase Ollama, `OllamaReasoner.reason()` (tier.2), preparse path. Root cause of 3-minute turn latency was yoga9i blocking — gate fixes this.

**G57 — NE idle gate + double-fire lock** ~~CLOSED 2026-03-12m~~
TWM fingerprint (`twm_count()` + `twm_max_id()`) — NE skips if unchanged AND < 2min cooldown. `threading.Lock` prevents double-fire. Both added to main.py `_run_ne_background()`. Eliminates wasteful NE runs when nothing changed.

**G58 — Preparse short-input skip** ~~CLOSED 2026-03-12m~~
`_short_input = len(user_input.split()) <= 6` added to `_skip_llm_preparse` conditions. Greetings and one-liners skip Ollama preparse entirely; also gated by `_cloud_mode_active`.

**G59 — Console timestamps** ~~CLOSED 2026-03-12m~~
`cts()` in `cognition/forensic_logger.py` returns `HHmmss ` prefix. Imported in `main.py` and `narrative_engine.py`. All `[dim]` console prints prefixed. Dashboard has 4-section redesign: Graph / Inference / Performance / How-he's-doing; `inference_data: dict` parameter carries tier/tokens/cost/latency per turn.

**G60 — Tier model inversion fix** ~~CLOSED 2026-03-12m~~
Bug: `openrouter_interactive_reasoner` was using `OPENROUTER_INTERACTIVE_MODEL=sonnet`. Both tier.3.5 and tier.4 were sonnet. Fixed: tier.3.5 → `OPENROUTER_DEFAULT_MODEL=haiku`; tier.4 → `OPENROUTER_INTERACTIVE_MODEL=sonnet`. Result: $0.014-0.016/turn (was $0.05-0.24).

**G61 — NE narrative as temporal thread anchor (#195)** ~~CLOSED 2026-03-12n~~
NE tags narrative `write_ring()` with active `thread_id` (most common in obs_list). `_build_session_context()` finds most recent `narrative` ring entry (≤10 min) for current thread, emits `[Thread arc: {summary}]` as anchor, then only ≤5 delta ring entries since anchor. Falls back to 10-entry block if no anchor. Effect: 3-6× less context per turn once NE has run.

---

## Update: Session 2026-03-12o — Pipeline Trace + Routing Introspection

### Resolved

**G62 — Pipeline trace instrumentation** ~~CLOSED 2026-03-12o~~
`forensic_logger.py`: added `set_turn_id()`/`get_turn_id()` (threading.local), `log_pipeline_step()` appending to `pipeline_trace.YYYYMMDD.log` (24h rotation, purges >1 day). `main.py` instruments all named stages: `thalamus | bg_prospect | preparse_search | routing | habit_exec | think_build | think_llm | winnow | reasoning | mem_store | TOTAL`. `base.py` `_winnow_context()` logs `winnow` step via `get_turn_id()`. Replaces 3-coarse-segment `latency_trace` with per-step resolution for data-driven bottleneck identification.

### Still Open

**G63 — Routing self-awareness: Igor's plans contradict D035** ~~CLOSED 2026-03-14c~~
**Observed (2026-03-12o)**: Igor wrote plans claiming "Local inference" for interactive turns — contradicts D035 (interactive→tier.3.5 floor unconditionally). 100% of interactive turns in logs escalate to haiku/sonnet regardless of complexity signal.

**Fix**: Sent CC bridge message to seed `PROC_ROUTING_INTROSPECTION` habit with accurate D035 description. Igor confirmed seeded, blob stored (`68e63a31`), G63 closed.

**Result**: Igor now has accurate self-model of routing stack in PROCEDURAL memory. Plans involving "local inference" will correctly be scoped to background/NE work only.

**Secondary (CLOSED 2026-03-12o)**: IMPULSE_SKIP root cause was `OllamaReasoner.reason()` raising `RuntimeError("cloud_mode active")` unconditionally — it didn't check whether the call was interactive or background. Fix: `force_local=True` (already set by main.py for impulse paths) now propagates from `OllamaPool.reason()` into `OllamaReasoner.reason()`, bypassing the cloud_mode gate. Background/NE turns run as long as they need. Interactive turns still escalate via D035.

- **#192** — InferenceGateway: unified routing abstraction
- **#193** — Active jobs surface via TWM
- **#189/#190** — Remote Igor instances
- **#187** — Igor's own GitHub identity
- **G37 Phase 2** — dual word graphs
- **G48** — Mobile + offline sync epic
- **G46** — Memory model fields: source, confidence, context_of_encoding (HIGH inertia, design carefully)

## Update: Session 2026-03-12p — Self-repair / Turn Revision Detection

### Resolved

**G64 — Self-repair: turns that revise prior statements** ~~CLOSED 2026-03-12p~~

**Observed**: Debounce (#146) was a timing bandaid — it batched rapid successive messages into one turn by merging them with `\n`. This worked when revision arrived within DEBOUNCE_SECS but (a) merged them without modeling the relationship, and (b) didn't handle cross-turn revisions (Igor had already responded to the first message).

**Root cause**: The utterance pattern "Yes, I can do that! [END OF TURN] Oh wait, I can't because X" is a **self-repair** in conversation analysis — message N+1's meaning is semantically dependent on and modifies message N. Treating them as independent statements or naively joining them loses the revision relationship.

**Fix (two paths)**:
1. **Same-batch merging (`_smart_merge()`)**: When debounce fires with multiple buffered messages, `_smart_merge([texts])` checks if any message after the first contains a repair marker (`"oh ", "wait", "actually", "hold on", "never mind", "i can't"`, etc.). If yes, output is `[STATEMENT]: ... \n[REVISION]: ...` instead of plain `\n`-join. Applied to stdin flush (all 3 flush points) and `_flush_debounced_network()`.
2. **Cross-turn detection (`_detect_self_repair()`)**: At the top of `_process_inner()`, before thalamus, check ring_memory `user_turn` entries for the last human turn. If age < `_REPAIR_WINDOW_SECS` (90s) AND new input contains a repair marker, write a `[SELF-REPAIR]` ring entry with `category="self_repair"`. Ring entries flow into LLM context via `_build_ring_context()` (not in `_RING_EXCLUDE`). LLM sees: "Prior: '...' — Revision: '...'. Interpret revised meaning; original commitment is retracted."

**Result**: Igor now models the revision relationship explicitly rather than treating the second message as a standalone statement or silently merging both. The debounce still fires (avoids processing partial input) but the output is semantically labeled when revision is detected.

---

## Update: Session 2026-03-13a — Non-blocking concurrent turn processing

### Resolved

**#200 — Non-blocking network dispatch** ~~CLOSED 2026-03-13a~~

**Observed**: `_process()` is synchronous. Web messages were buffered 3s (DEBOUNCE_SECS) before dispatch, then blocked the main loop for the full LLM call duration (~30-120s). A second message arriving while LLM in-flight would also wait 3s + be serialized behind the first.

**Root cause**: Single-threaded model where all inference ran in the main loop. `_drain_network()` buffered messages into `_net_debounce` dict; `_flush_debounced_network()` processed them inline.

**Fix**:
1. **Removed** `_net_debounce`, `_flush_debounced_network()`.
2. **Added** per-thread-id `queue.Queue` + daemon worker thread (`_thread_queues`, `_thread_workers`).
3. **`_drain_network()`** now dispatches immediately via `_enqueue_network_msg()` for regular messages. CC bridge and slash commands still processed inline (fast, ordering-critical).
4. **`_thread_worker(thread_id, q)`**: drains queue sequentially; exits after 5s idle; restarted on next message. LLM calls happen here, never in the main loop.
5. **Stdin debounce** reduced from 3000ms to 500ms (handles multi-line pastes; terminal only).

**Result**: Web messages dispatched within one main loop tick (≤0.5s). LLM inference in worker threads. Main loop keeps running during inference. Second message arrives while LLM in-flight → queued, processed sequentially after. G64 cross-turn self-repair still works via ring_memory.

---

## Update: Session 2026-03-13a (continued) — Tiered log hierarchy (#201/#202/#203)

### Resolved

**#201 — interaction.log** ~~CLOSED 2026-03-13a~~

One line per non-impulse turn appended to `interaction.YYYYMMDD.log`. Format: `timestamp|turn_id|thread_id|tier|elapsed_ms|$cost|IN:preview|OUT:preview`. Daily rotation, 7-day retention. The first log to read — `turn_id` is the join key to all others.

**#202 — startup.log** ~~CLOSED 2026-03-13a~~

One structured block per boot appended to `startup.log`. Contains: memory count, habit count, word graph size, component health (ollama, openrouter), warm context status. Keeps last 50 boots (trims oldest on write). Immediate answer to "was the boot clean?"

**#203 — turn_trace.YYYYMMDD.log** ~~CLOSED 2026-03-13a~~

Full TurnContext dict (JSON) per turn. `threading.local` dict built up by `log_pipeline_step()` (dual-use — no new call sites for existing stages) + new `init_turn_ctx` / `finalize_turn_ctx` bookends in `_process_inner()`. Daily rotation, 2-day retention. Gate: `IGOR_TURN_TRACE` (default true). `/trace N` command prints last N traces.

**Triage workflow:**
1. `tail interaction.log` → spot bad turn + turn_id
2. `grep <turn_id> inference_io.log` → see raw LLM I/O
3. `grep <turn_id> turn_trace.log` → see full state machine (thalamus/routing/habit/cost)

---

## Update: Session 2026-03-13c — Habits, temporal anchoring, book learner, db_proxy commit fix

### Resolved

**G65 — score_memories() bottleneck** ~~CLOSED 2026-03-13b~~

`score_memories()` called `qwen2.5:7b` on every interactive turn (25–200s). `cortex.search()` Phase 2 cosine rerank is better quality anyway. Removed from both `_skip_llm_preparse=True` and `=False` branches in `main.py`. Result: `preparse_search` p50 ~500ms.

**G66 — habit trigger matching** ~~CLOSED 2026-03-13c~~

`_score_habit()` treated multi-word triggers as a single substring (`'hello hi hey...' in 'hello'` → always False). Zero habits fired. Fixed with three-format dispatch in `basal_ganglia.py`: pipe-separated (`hello|hi|hey`), legacy space-separated with min-5 token filter, single-token. PROC_GREETING now fires.

**G67 — db_proxy silent rollback** ~~CLOSED 2026-03-13c~~

`_DBContext.__exit__()` closed the SQLite connection without calling `commit()`. Every write through `cortex.store()` was silently rolled back. Discovered when `book_learner.py` reported "10 nodes deposited" but DB showed zero. Fix: `commit()` before `close()` when no exception; `rollback()` on exception. This affected all writes since DatabaseProxy was introduced.

**G68 — habit response fallback** ~~CLOSED 2026-03-13c~~

Habits with no `action` key in metadata showed `"Habit executed. [PROC_xxx: ...]"` to users. Added `actions` list support in `main.py` (random choice for natural variation). PROC_GREETING updated with 7 igorish response variants. Other habits that had this problem (PROC_READING_DEPOSIT, PROC_WG_PREPARSE_TUNING) also fixed.

**G69 — temporal anchoring** ~~CLOSED 2026-03-13c~~

Memories injected into LLM context had no creation date. Igor treated a memory from 2023 the same as one from today. Fixed in `_build_memory_context()` (shows "stored 45d ago (2026-01-27)") and `_build_ring_context()` (ring entries show `YYYY-MM-DD HH:MM` when not from today). Igor can now distinguish past from present.

### New

**G-BL1 — book learner habit** *(~1h)*
`claudecode/book_learner.py` exists but no PROC habit wires to it. Igor can't invoke it himself yet.

**G-BL2 — reading interest gate** *(~2h, #214)*
Igor can't say "this no longer interests me" to stop slow reading. Needs TWM signal + habit that sets a stop flag checked by `ebook_reader`.

### New tool: `claudecode/book_learner.py`

Chunks a book via `ebook_reader`, sends each chunk to gpt-4o-mini with an extraction prompt, deposits FACTUAL/INTERPRETIVE/PROCEDURAL nodes into Igor's graph via `cortex.store()`. Checkpoint/resume support. Trains word graph per chunk as side effect. Cost: ~$0.02 for a 300-page book. First run: 10 chunks of Damasio "Feeling of What Happens" → 44 nodes deposited.

---

---

## Update: Session 2026-03-13e/g — Reading pipeline fixes

### Resolved

**G70 — fiction author filter missed known authors** ~~CLOSED 2026-03-13e~~

`_is_fiction()` checked Calibre tags only. Authors with no/wrong tags (Piers Anthony, Pratchett, etc.) passed the filter. Fixed: `_FICTION_AUTHORS` set in `learner.py`; `author_sort` checked before tags. Auto-discovery now correctly skips known fiction authors.

**G71 — book learner Ollama model parse error** ~~CLOSED 2026-03-13e~~

`OLLAMA_LOCAL_MODEL` env var had an inline comment (`# upgraded from llama3.2:1b`). Entire string including comment was sent to Ollama → HTTP 400. Fixed: `.split("#")[0].strip()` in `book_learner._extract_nodes_local()`. Local timeout bumped 60→300s for CPU inference.

**G72 — NE JSON parse failures silent** ~~CLOSED 2026-03-13g~~

gpt-4o-mini returned prose-wrapped JSON for NE calls. `_parse_ne_json()` silently dropped the response; only "skipping cycle" logged with no diagnostic. Fix 1: `inference_gateway.py` NE purpose extra now includes `response_format={"type":"json_object"}` — OR contractually returns valid JSON. Fix 2: `narrative_engine.py` prints `raw[:150]` + calls `log_anomaly(NE_FAIL, json_parse_failed)` on parse failure.

---

## Update: Session 2026-03-14a — Planning: overnight learning pipeline + Igor web identity

### No gaps closed (planning session)

### New Gaps

**G73 — overnight reader stops after first book** ~~CLOSED 2026-03-14b~~

Fixed by `claudecode/drain_learn_queue.py`: loops over `learn_queue.json` until all items are done; PID-guarded against duplicate runners; 60s between launches; auto-spawned by `learn_about()` whenever items are queued. `drain_learn_queue` tool added to tool registry for manual trigger.

**G74 — no autonomous source discovery** *(#215, ~3h)*

Topic → reading list requires manual URL curation. No TopicExpander exists. Fix: given a topic string, call a free AI web interface via anonymous browser_use; parse returned URLs into LearningQueue as `pending_fetch`. Local Calibre index CSV queried for matching books as priority source.

**G75 — no LearningQueue / NightlyRunner infrastructure** *(#215, ~1 day)*

No persistent queue, no rate-limited parallel fetcher, no blob→book_learner trigger, no overnight scheduler. These are all separate from the existing `book_learner.py` (which runs one book synchronously). Fix: build LearningQueue (SQLite-backed), ParallelFetcher (rate-limited per domain, parallel across), NightlyRunner (cron-triggered, drains queue, logs to `nightly_learning.log`).

### Decisions made

- **D054**: anonymous browser_use for AI consultation (no API key needed — free AI web UIs work without login)
- **D055**: Igor's own Chrome identity (theigorsigor@gmail.com) — one login unlocks all Google services; better than one API key per service; Igor creates his own accounts on new services using that email
- **D056**: curriculum order: language → cogsci → how Igor works → programming/AI → culture. Language first because the word graph IS a language model — Igor reads about himself before knowing it. "How Igor works" before AI/programming to build self-knowledge from first principles before external ML framing.

### New issues

- **#215** — Epic: Fully Automated Overnight Learning Pipeline
- **#216** — Epic: Igor browser identity (Chrome as theigorsigor@gmail.com; supersedes #186 OAuth approach)
- **#217** — chore: Ebook library index — Calibre scan + CSV catalog

### Session 2026-03-14b additions

- **D057**: three-tier runtime model — machine-global / database-global / instance-local; baked into #197
- **D058**: skills as compiled executive functions — `/igor`, `/workstep`, `/validate-files` skills
- **D059**: `capabilities_index.dsb` — 118-tool inventory, one line per tool
- **D060**: research delegation to Igor at tier.3 (cheap) for bulk fact-gathering; output as topic DSBs

New issues:
- **#218** — design_docs/ cleanup: archive CSBs, create human-readable doc set

### Session 2026-03-14g additions

- **G-BRW2 ~~CLOSED~~**: User applied `OLLAMA_HOST=0.0.0.0` to `/etc/systemd/system/ollama.service.d/override.conf` + daemon-reload + restart; cluster_status can now reach Ollama via external IP
- **G-BRW3 ~~CLOSED~~**: `restart_ollama(machine="")` tool in cluster_ssh.py — local uses `sudo systemctl restart ollama.service` (sudoers entry added); remote uses `_ssh_run()` + sudo; 5s wait + health check. `_try_restart_local_ollama()` in inference_gateway.py — called from `is_local_inference_available()` when `is_healthy()` returns False; 60s cooldown; always-on; logs OLLAMA_RESTART_OK/FAIL/ERROR to forensic logger
- **G-BRW4 (new, closed)**: browser_use 0.11.9 sent `minimum` property on integer schema fields; Claude-sonnet-4-6 via Anthropic rejected with HTTP 400 on every step. Fix: upgraded browser-use to 0.12.2; fixed `result.final_state().url` → `result.urls()[-1]` (API removed in 0.12.x). Result: browser discovery working.
- **G-BRW5 (new, open)**: topic extraction received full CC bridge thread context as `user_input`; `_extract_topic()` used `startswith()` so returned full blob as topic. Fix applied: changed to `find()` to search anywhere in input. Verify next session.
- **db_proxy SQL tracing**: `_DBContext` now uses `set_trace_callback()` to capture last SQL; slow query warnings include SQL snippet; dedicated `~/.TheIgors/logs/db_queries.log` with `turn=` tie-back to forensic_logger
- **G-DBM1 (new, open)**: `last_accessed=None` on all memories including all CPs — `record_activation()` only called on habit fires, never on `search()` results. Fix: update `last_accessed` on memories surfaced into LLM context (top-N from search + interpretive traversal). Blocked by: need slow query baseline first before adding more writes.
- **browser_use LLM**: switched to `gpt-4o-mini` via OR (cheaper; avoids Anthropic schema strictness); `BROWSER_USE_MODEL` env var overrides; browser still opens on real display while debugging (will force Xvfb once stable)
- **sudoers entry**: `akien ALL=(ALL) NOPASSWD: /bin/systemctl restart ollama.service` added

### Session 2026-03-14f additions

- **PROC_CLUSTER_SSH_CHECK fixed**: `code_ref` had `_cluster_status` (wrong, private name) → `cluster_status` (registered tool name); fixed via DB UPDATE
- **Ollama service fixed**: snap Ollama was holding port 11434 with no models; stopped + disabled; systemd Ollama now running with nomic-embed-text + qwen2.5:7b + llama3.2:1b; external IP still needs `OLLAMA_HOST=0.0.0.0` in `/etc/systemd/system/ollama.service.d/override.conf`
- **Planned (next session)**: `restart_ollama` tool in cluster_ssh.py + auto-restart in inference_gateway.py when `is_healthy()` returns False; always-on, 60s cooldown, `sudo systemctl restart ollama.service`

### Session 2026-03-14e additions

- **G-RL2 ~~CLOSED~~**: browser discovery now working — 3 bugs fixed in `learner.py`/`browser.py`; 20 URLs queued for Pinker/Tomasello/Lakoff; drain runner active
- **browser.py**: `_ensure_virtual_display()` added — uses pyvirtualdisplay/Xvfb; no longer opens on user's desktop
- **Claude Code hooks**: PostToolUse auto-format (black) + PreToolUse dangerous-bash guard wired in `~/.claude/settings.json`; scripts in `~/.claude/hooks/`
- **CLAUDE.md Compact Instructions**: section added; guides auto-compact summarizer to preserve open gaps, modified files, current hypothesis
- **WorkingWithClaude.md**: skills/hooks/compact added to Infrastructure; Part Three "How I Work with Akien" added; workflow step 6 = notify user to /compact
- **New gap G-BRW1**: CC bridge messages fire PROC_GREETING instead of action habits for short action requests — PROC_GREETING threshold too high at tier.2; need habit scoring adjustment or CC bridge routing change
- **learner.py bugs fixed**: (1) `task=`→`task_description=` kwarg, (2) json.loads() before dict access, (3) pyvirtualdisplay installed

### Session 2026-03-14d additions

- **browser_use confirmed available**: v0.11.9 in venv — earlier "not installed" check was wrong (used system Python, not venv)
- **G-RL2 in progress**: Lakoff *Metaphors We Live By*, Pinker *Language Instinct*, Tomasello *Constructing a Language* — none in Calibre or SORTUS-EBOOKS; Igor sent CC bridge message to queue all three via `learn_about()` for overnight drain runner
- **Library state**: Calibre has Lakoff *Political Mind* (IDs 2241/3495); Pinker and Tomasello absent entirely; future G: Igor to deduplicate/index his own library

### Session 2026-03-14c additions

- **G63 closed**: PROC_ROUTING_INTROSPECTION seeded via CC bridge; Igor confirmed and stored blob
- **PROC_RELOAD_AFTER_EDIT implemented**: `_try_hot_reload()` in `self_edit.py` — auto-reloads LOW-inertia modules post-edit when `IGOR_HOT_RELOAD=true`
- **#205 (partial)**: 4 LOW-inertia silent except-pass fixed with `log_error()` — ebook_reader.py (3), learner.py (1); MEDIUM-inertia files (basal_ganglia, narrative_engine, inference_gateway) deferred
- **Latency investigation**: no bug — slow haiku calls are agentic sessions with 19-42 turns under `IGOR_MAX_TURNS=50`; interactive haiku healthy at 7-9s
- **#218 closed**: 28 stale CSB/MD files archived to ~/TheIgorsProject/akien/Readings/; 9 new human-readable docs created in design_docs/ (ProjectOverview, OverallArchitecture, DesignDecisions, 6 subsystem docs); WorkingWithClaude.md moved from thoughts/

*Updated: 2026-03-14c by Claude Code.*
