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
- **G-BRW5 ~~CLOSED~~**: topic extraction now correct — `_extract_topic()` find() fix confirmed working via CC bridge; "go learn about mathematics" → topic="mathematics" (clean). Browser discovery triggered and found 9 books via Gemini but returned 0 direct URLs — ChatGPT/Gemini responses are prose, not hyperlinks. URL extraction from prose is G74 (open). G-BRW5 (topic extraction) closed.
- **db_proxy SQL tracing**: `_DBContext` now uses `set_trace_callback()` to capture last SQL; slow query warnings include SQL snippet; dedicated `~/.TheIgors/logs/db_queries.log` with `turn=` tie-back to forensic_logger
- **G-DBM1 ~~CLOSED~~**: `cortex._touch_last_accessed()` — single SQL `UPDATE last_accessed` for top-N memories returned by `search()`, at both Phase 2 (embedding) and Phase 1 fallback paths. Skips ROOT/CP structural nodes. Verified: 10 memories got timestamps after first test turn post-restart.
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

### Session 2026-03-14j additions

- **G-SP1 ~~CLOSED~~**: `self_edit.py` — `_push_edit_episodic()` added; `_try_hot_reload()` now accepts `reason` param and always pushes EPISODIC memory (portable=False, source="self_edit") before attempting hot-reload. Both callsites (edit_source_file + patch_source_file) pass reason through. D070 implemented.
- **filesystem.py**: `_resource_load_dict()` now includes `night_mode` (1 if 22:00-07:00, else 0) — enables threshold habits gated on time of day.
- **G-HB1 ~~CLOSED~~**: PROC_RESOURCE_AWARENESS trigger had "memory" — matched cognitive questions ("what do you know about memory and emotions") instead of resource-load questions. Fix: removed "memory" from trigger in live DB directly (`UPDATE memories SET metadata=... WHERE id='PROC_RESOURCE_AWARENESS'`). Seed script `seed_resource_gate_habits.py` still has old trigger — fix on next reseed.
- **G-HB2 (new, open)**: "log a ticket that you're still having trouble sshing to yourself" → PROC_GREETING fired. PROC_GREETING trigger is clean (hello|hi|hey|...). Unknown cause — possibly a self-seeded habit with broad triggers. Needs: query live DB for habits matching "log" or "ticket".
- **G-CK1 ~~CLOSED~~**: cloud_ok master switch fully implemented. `cloud_mode.py`: `is_cloud_ok_override()` reads `~/.TheIgors/cloud_ok_override.json` (TTL-based); `set_cloud_ok_override()` / `clear_cloud_ok_override()`. `inference_gateway.py`: `cloud_ok_override` field in `InferenceContext`; `_cloud_ok()` + `_cloud_preferred()` gate on it for background calls. `book_learner.py`: `_should_use_local()` reads override per-chunk. `drain_learn_queue.py`: `_is_cloud_ok_override()` belt-and-suspenders at launch. `learner.py`: `cloud_ok` in queue items; "now" writes override, "tonight" clears it. Habits seeded: PROC_SET_CLOUD_NOW + PROC_NIGHT_READ. D071.
- **G-RL3 partial**: `cloud_ok` field in queue items + drain runner updated + override set/clear wired. Still open: `reading_list` status updates (in_progress/completed) and full PROC_NIGHT_READ wiring to reading_list table.

### Session 2026-03-14i additions

- **G74 partial fix**: `learner.py` — `_discover_urls_direct()` added: constructs arXiv/Wikipedia/Gutenberg URLs directly without needing AI response (always delivers 3 URLs per topic). `_DISCOVERY_PROMPT` updated to force bare-URL-per-line output. `_parse_urls()` now also extracts markdown `[text](url)` links + deduplicates. Wired into `learn_about()`: direct channel runs first, then AI browser channel.
- **Learn queue cleanup**: 10 corrupt entries (old thread-context pollution from before G-BRW5 fix) removed; 9 targeted linguistics URLs added (Wikipedia: language acquisition/universal grammar/cognitive linguistics/construction grammar; SEP: language+thought/linguistics; arXiv x3); drain runner started.
- **#205 silent exception audit (MEDIUM files)**: Full audit of basal_ganglia.py, narrative_engine.py, inference_gateway.py, thalamus.py, learner.py — all 51 exception handlers reviewed; all are intentional (optional instrumentation, safe degradation, or tier-cascade). No fixes needed.
- **D069**: reading mode sympathetic/autonomic — `cloud_ok` field in queue items; "tonight" = background/local-only (cloud_ok=False); "now" = foreground/cloud-OK. Encodes parasympathetic vs sympathetic at queue level.
- **D070**: G-SP1 pattern — after `self_edit.patch_source_file()` succeeds: push EPISODIC memory of edit, then call `reload_module()` directly. Both awareness (memory) and automation (direct call). No habit needed.
- **#219 created**: feat: PROC_NIGHT_READ habit + tonight/now reading modes (G-RL3)
- **Plan approved**: G-SP1 (self_edit.py: episodic memory push + reload_module call) + G-RL3 (cloud_ok field, tonight/now parsing, PROC_NIGHT_READ seed)

### Session 2026-03-14h additions

- **G-BRW1 ~~CLOSED~~**: Two-part fix — (1) `basal_ganglia.py` Format 1 pipe triggers now use `\b`-bounded regex (prevents "hi" matching inside "this"); (2) `thalamus.py` strips `[Routing directive:...]` suffix from `core_text` before habit scoring. Result: `/metrics` and `reload_module(...)` no longer fire PROC_GREETING; `hello` still routes correctly.
- **G-BRW5 ~~CLOSED~~**: Confirmed — topic extraction works via CC bridge; "go learn about mathematics" → topic="mathematics". Browser discovery triggered and queried Gemini+ChatGPT; got book titles but 0 direct URLs (prose responses). URL extraction from prose is G74.
- **New gap G-RD1 (new, small)**: `[Routing directive:...]` was leaking into single-arg habit code_ref tool calls. `main.py` line 2921 passed `user_input` (raw) to tool; now passes `parsed.core_input` (routing directive stripped). Fixed same session.
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

### Session 2026-03-14l additions

- **G-MP1 ~~CLOSED~~**: D072 vigilance gate implemented. `word_graph.py`: `predict_next_with_flatness()` convenience wrapper added. `main.py` `_build_think_context()`: if `self._npass_reply` and generation graph present, runs `predict_next_with_flatness(user_input, n=5)` — injects `[REFLEXIVE_PATTERN]` when flatness < 0.35 (steep = reflexive path), `[GRAPH_UNCERTAIN]` when > 0.85 (novel/graph-empty). Forensic debug log. Gate: `IGOR_NPASS_REPLY=true` (added to .env). Zero extra LLM calls.
- **G-HB2 ~~CLOSED~~**: Root cause confirmed — all logged misfires are from before D066 (committed 15:33 2026-03-14). Pre-D066 pipe-trigger matching used plain substring (`"hi" in text`), matching `"hi"` inside `"relationship"` and similar. D066's `\b` word-boundary regex already fixed this. No new code needed.
- **G-RL3 ~~CLOSED~~**: `drain_learn_queue.py` — `_set_reading_list_in_progress(calibre_id)` added; called after successful Popen launch for calibre entries; sets `status='in_progress'`, `started_at=now` where `status='queued'`. `book_learner.py` — at end of full run (`position >= total_sentences` and no `--limit`), sets `status='completed'`, `completed_at=now`.

### Session 2026-03-15a additions (overnight analysis + workstep plan)

- **G-OVN-1 (open)**: 10/13 regression phrases hit wrong habits. PROC_SWAP_THRESHOLD fires for "most vivid memory"/"how old is your oldest memory" (trigger contains "memory"). PROC_CALENDAR_CREATE fires for "what do you remember from yesterday". PROC_CLUSTER_SSH_CHECK fires for any question with "fields"/"understand". Fix: intent gate in basal_ganglia — skip threshold/tool-dispatch habits when intent=question/introspective_question. Issue #222.
- **G-OVN-2 (open)**: `ebook_reader.read_chunk` calls `cortex.twm_push(content=...)` but signature wants `content_csb=`. 799 errors logged. Reading→TWM pipeline completely dead. One-line fix. Issue #223.
- **G-OVN-3 (open)**: drain cron uses relative path `claudecode/drain_learn_queue.py` → resolves to `/home/akien/claudecode/` (not in repo). Silent failure every 30min since setup. Fix: absolute path in crontab. Issue #224.
- **G-OVN-4 (open)**: book_learner `--local` flag + 8 concurrent processes → Ollama 404 on every chunk. 400+ chunks processed, 0 nodes deposited. Only cloud (gpt-4o-mini) succeeded (154 nodes from Wikipedia: language). Fix: remove `--local`, cap concurrency, add cloud fallback. Issue #225.
- **G-OVN-5 (open)**: `learn_about` called 6+ times with raw CC bridge thread-context prefix as topic. `_extract_topic()` not stripping CC format. Fix: add CC prefix patterns to strip list in learner.py. Issue #226.
- **Memory**: 8,061 → 8,460 (+399 overnight). FACTUAL +222, EPISODIC +112 (thin NE traces). 154 nodes from Wikipedia: language are quality content.
- **phrase_regression.py**: created `claudecode/phrase_regression.py` — sends test phrases via CC bridge at configurable interval, random order, N passes. Log: `~/.TheIgors/logs/phrase_regression.log`. First run overnight with 13 phrases, 2 passes, 5min delay.
- **Workstep plan for 2026-03-15**: fix G-OVN-2 (1 line) → G-OVN-3 (cron) → G-OVN-4 (drain) → G-OVN-1 (habit intent gate, coherence breakthrough) → G-HB3 (#220) → G-QP2 (#221 LIMIT).

### Session 2026-03-14m additions

- **G-HB3 (new, open)**: Introspective inputs ("what are you inside", "tell me about the igors") route to `PROC_RESP_WHO_AM_I` habit, which returns a canned string. D072 vigilance gate never fires — habits bypass `_build_think_context()` entirely. Fix direction: convert `PROC_RESP_WHO_AM_I` from response habit to context-injection habit (inject LTM query + milieu state as LLM context, let LLM answer). Issue #220.
- **response_quality_cases.md**: Created `design_docs/response_quality_cases.md` — 6 manual regression test cases (TC-1 through TC-6). Each has: input text, expected behavior, known failure mode, what to watch for in web log. TC-3 documents G-HB3. TC-6 ("tell me about the igors") documents first-person interiority check.
- **Naming discussion**: "ingest" proposed as unified term replacing separate "word_graph training" / "reading pipeline" concepts. Slow_read (per-book process) vs bulk_load (parallel ingest) naming for #RL1 process split. Also: drain_learn_queue.py system cron check — confirm it's running as a system cron, not just manually.

### Session 2026-03-14n additions

- **G-QP2 (new, open)**: DB grown to 8,132 memories from overnight book loading. Three query patterns consistently slow: (1) NE activation scan `SELECT * ... NOT IN ('ROOT','CORE_PATTERN') ORDER BY activation_count DESC` — p50=628ms, p99=1100ms — index used but SELECT * fetches all 8,125 rows; fix: add LIMIT 100. (2) EPISODIC fetch — p50=175ms — returns 4,294 rows; fix: LIMIT + column projection. (3) id IN PK lookups — p50=131ms — WAL contention; fix: PRAGMA wal_checkpoint(TRUNCATE) at boot. Issue #221.
- **System crons wired**: drain_learn_queue.py every 30min; CC-bridge nudge ("keep picking up language") every 4 hours. Logs: `~/.TheIgors/logs/drain_cron.log`, `nudge_cron.log`.
- **DSB format decision**: new GitHub issues = English header + DSB body; GitHub discussion #62 session entries = full DSB going forward.

### Session 2026-03-14k additions

- **G-QP1 ~~CLOSED~~**: `SELECT * FROM memories WHERE memory_type NOT IN ('ROOT','CORE_PATTERN') ORDER BY activation_count DESC` was running 600–750ms on every NE cycle. Fix: added `CREATE INDEX IF NOT EXISTS idx_activation ON memories(activation_count DESC)` to `cortex.py` `_init_db()`. Index also applied to live DB directly. EXPLAIN QUERY PLAN confirms `SCAN memories USING INDEX idx_activation` — sort eliminated.

**G-MP1 — Multi-pass response generation** *(urgent, ~2h — design complete, ready to implement)*

Akien's observation: Igor's responses feel "too automatic, too low level." Single-pass LLM output bypasses the inhibition layers that human (and internal narrative) processing goes through.

**Design direction (2026-03-14k) — build like the biology:**

The narrative engine IS the TWM — not two separate things. The TWM is the current activation state of the graph; the NE is the process traversing that state, predicting what fires next; the predictions ARE the next activations. Key science: Global Workspace Theory (TWM = broadcast workspace; narrative = competitive broadcast process), Attractor dynamics (loop terminates at stable state not by step count), ART vigilance gate (match above threshold → commit; below → reject and search), spreading activation (concurrent waves, not sequential BFS).

**The problem:** no lateral inhibition. The highest-weight path wins immediately. `gradient_flatness()` on the generation graph IS the vigilance signal — fast settle (high flatness immediately) = reflexive answer = below-vigilance = reject.

**Implementation — no extra LLM call:**
1. Before reply LLM call, run `predict_next()` on generation graph seeded by current context + compute `gradient_flatness()`
2. If flatness > `NPASS_FLATNESS_THRESHOLD` → inject into think context as `[REFLEXIVE_PATTERN]: your generation graph predicts: {words}. If this feels too automatic, go deeper.`
3. Single LLM call self-inhibits the obvious path. Inhibition happens BEFORE output (biology-correct). Cost: `predict_next()` + `flatness()` = microseconds.

**Files:** `word_graph.py` (LOW) — expose `predict_next_with_flatness(seed_words)`. `main.py` (MEDIUM) — `_build_think_context()`: add generation graph prediction + REFLEXIVE_PATTERN injection. Gate: `IGOR_NPASS_REPLY` (already exists).

**When to escalate to LLM (D073):** `gradient_flatness()` gives two signals: (1) HIGH immediately = reflexive, inhibit and re-traverse (D072); (2) NEVER converges after enough cycles = genuinely exhausted = escalate. "I honestly looked everywhere and I'm stumped" — not a canned fallback. Factual queries: achievable soon. Fuzzy/generative: harder, deferred. "The program is the data" — the graph IS the knowledge; LLM is the trainer, not the primary answerer. Book learning pipeline unchanged; this changes when we query the graph vs. hand off.

**Dependency:** enable `IGOR_DUAL_WORD_GRAPHS` first (seed script exists) — need reply data in the generation graph before flatness is meaningful. D072 + D073.

*Updated: 2026-03-14k by Claude Code.*

### Session 2026-03-15b additions (overnight fixes: all 6 workstep items)

- **G-OVN-1 ~~CLOSED~~**: `basal_ganglia.py` intent gate: skip `habit_type="threshold"` always; skip `habit_type in ("action","proactive")` with `code_ref` + `habit_type in ("workflow","delegation","reactive")` when `parsed_intent in _QUESTION_INTENTS`. Verified: "What do you remember from yesterday?" no longer fires PROC_CALENDAR_CREATE; "Tell me about fields you need to understand" no longer fires PROC_CLUSTER_SSH_CHECK. Root cause was habit trigger vocabulary (e.g. "remember" in PROC_CALENDAR_CREATE) overlapping common question words. Two DB trigger fixes: PROC_CALENDAR_CREATE → pipe-separated specific calendar phrases; PROC_RESP_CLARIFY → pipe-separated (prevented "understand" keyword from matching cognitive questions). Commits: 326f433, c8e8f79. Issues #222.
- **G-OVN-2 ~~CLOSED~~**: `ebook_reader.py` line 762 — `content=` → `content_csb=` on `cortex.twm_push()` call in `read_chunk()`. 799 silent failures since reading pipeline started. Reading→TWM pipeline now live. Commit: 326f433. Issue #223.
- **G-OVN-3 ~~CLOSED~~**: System crontab drain cron now uses absolute path `/home/akien/TheIgors/claudecode/drain_learn_queue.py`. Issue #224. (Fixed prior session via sed+crontab.)
- **G-OVN-4 ~~CLOSED~~**: `drain_learn_queue.py` — `_count_running_learners()` via `pgrep -fc book_learner.py`; `MAX_CONCURRENT=2` gate checks before each `_launch()` call; sleeps + continues if at cap. Issue #225. Commit: 326f433.
- **G-OVN-5 ~~CLOSED~~**: `learner.py` `_extract_topic()` — strips `[Thread context: ...]` + `[xxx]: ` CC bridge prefixes before trigger search; returns `""` if < 2 trigger words or < 3 total words after stripping. Issue #226. Commit: 326f433.
- **G-HB3 ~~CLOSED~~**: `main.py` — new `context_inject` habit type handler (before `if habit:` block): fetches identity+CP memories via `cortex.search()`, gets milieu state, pushes `SELF_CONTEXT|milieu=...|{id_lines}` to TWM (salience=0.75, ttl=90s), sets `habit=None` to fall through to LLM. `PROC_RESP_WHO_AM_I` DB updated: `habit_type="context_inject"`, trigger converted to pipe-separated (`what are you made of|who are you|...`), `context_query` added. Result: introspective questions get real LLM answers using identity context. Verified: `habit_fired: true` in turn trace + rich architectural response. Issue #220. Commit: 326f433.
- **G-QP2 ~~CLOSED~~**: `cortex.py` `search()` Phase 1 query: added `LIMIT 300` to candidate pool fetch (`ORDER BY activation_count DESC`). `_init_db()`: added `PRAGMA wal_checkpoint(TRUNCATE)` at end of init block. Issue #221. Commit: 326f433. *Additional fix 2026-03-15: added three DB indexes directly in live DB — `idx_timestamp (timestamp DESC)`, `idx_type_timestamp (memory_type, timestamp DESC)`, `idx_source (source)`. NE episodic fetch dropped from 45-57ms to <3ms. No code change — indexes survive restarts.*
- **phrase_regression.py restarted**: 113-phrase file (`automated_phrase_response_test.txt`), 1 pass, 5-min delay. Running in background (PID 357138) after all fixes deployed.
- **Igor rebooted**: 08:08:26 on 2026-03-15. Memory count: 8,479 habits=101 (was 5,279/82 at session start).

### Session 2026-03-15e additions (memory architecture + three-session pattern + organizer)

**Design decisions recorded (not gaps — load-bearing architecture):**

- **Three-session CC pattern (D083, #249)**: Designer + Implementation Worker + Scribe Worker. Scribe handles all memory-coherence work (DSBs, GitHub, Igor flushes, commits). `flush_decision` / `flush_session` in `cc_queue.py` POST to Igor cc_notebook. `SCRIBE_CONTEXT.md` added as Scribe boot doc.
- **Issue filing = mini savestate (D084)**: each GitHub issue filing pushes the decision to Igor's memory immediately. Decision not made until in Igor's memory — DSB commit is durable backup, not primary record.
- **Training curriculum order (D085, #250)**: Layer 1 = Claude programming knowledge (organizational skeleton); Layer 2 = Akien's code + docs (lands on Layer 1 framework, used natively); Layer 3 = collaboration record (decisions_log + session narratives — what no other Igor will have). Order matters.

**G-QP2 additional optimization (2026-03-15):** Added three indexes directly to live DB: `idx_timestamp (timestamp DESC)`, `idx_type_timestamp (memory_type, timestamp DESC)`, `idx_source (source)`. NE episodic fetch: 45-57ms → <3ms. No code change needed — indexes survive restarts.

**G-NE1 — NE episodic-to-semantic merge** *(M — designed, not yet implemented)*

Current: each memory is a single narrative entry. Design (#250): `occurrence_dates` list in metadata — multiple occurrences of the same pattern stored as one semantic node with a list of when it occurred, not many EPISODIC entries. Enables proper semantic consolidation; frequency = semantic weight; NE can identify recurring patterns across sessions. Ticket: #250.

**New vision epics:**

- **#251 — Igor adaptive friction reducer (D086)**: milieu-driven interaction modes — high-energy: surface the lever; medium: walk through steps; low: do-the-thinking + queue + surface-one-thing. Data: Akien's writing patterns, Confluence, return frequency. Leah context with discretion.
- **#252 — Organizer knowledge base (D087)**: Igor researches Franklin/GTD/ADHD-productivity/motivational-science → high-inertia FACTUAL nodes; Akien annotates with personal experience; science + patterns + live-state = complete organizer substrate.
- **#253 — SuperClaude failover (D088)**: balance-check at launch: OR via API, Anthropic via Igor browser_use → `cc_channel/anthropic_balance.json`; pick endpoint + key before launching claude.

*Updated: 2026-03-15e by Claude Code (Scribe).*

---

### Session 2026-03-15f additions (Igor starts using his reading — winnow live, habits fixed, Workers headless)

**Decisions:**

- **D089 — headless Worker script**: `claudecode/worker` bash script — `claude -p` loop, one task per invocation, logs to `~/.TheIgors/logs/worker_role.log`; launch via `nohup ~/TheIgors/claudecode/worker &`. No terminal needed.
- **D090 — Scribe batch discipline**: Scribe self-directs from task log (reads Worker done messages, derives what docs changed); one commit per session when queue empties; Implementation Worker never queues Scribe tasks. `SCRIBE_CONTEXT.md` + `WORKER_CONTEXT.md` updated.

**G-OVN-1d — D074 expansion: response habits gate on knowledge_request (#254) ~~CLOSED~~**
`basal_ganglia.py`: added `knowledge_request` to `_QUESTION_INTENTS`; added G-OVN-1d gate — ALL response habits skip on `factual_question` or `knowledge_request`, fall through to LLM+winnow. PROC_RESP_DONT_KNOW trigger trimmed (removed `what do you know about`/`have you heard of` which were misfiring on knowledge queries). `cognitive`/`passive_capture` habits with no action template now fall through to LLM with `HABIT_FALLTHROUGH` ring entry instead of leaking debug text. PROC_LIST_ABSORBED_BOOKS trigger tightened. Issue #254.

**G-DSP1 ~~CLOSED~~**: Dashboard `Cloud%` label now distinct from CloudMode ON/OFF gate — Performance line shows `Cloud%: X%  CloudMode: ON/off`. p95 latency now filters out samples >60s before computing (excluded count shown when nonzero). Issue #247.

**G-RSP1 ~~CLOSED~~**: Three response bugs fixed: (1) `cognitive`/`passive_capture` habit fallthrough to LLM; (2) PROC_RESP_DONT_KNOW knowledge query misrouting; (3) G-OVN-1c suppress_on_factual_intent gate. Issue #248.

**G-QP2 ~~CLOSED (complete)~~**: COST DISCIPLINE habit (fba0d412) removed — superseded by inference gateway local-first routing. `IGOR_CONTEXT_WINNOW=true` enabled — 2278 FACTUAL reading nodes now reachable during conversations.

**Cortex performance (#258 + #258b)**:
- `_MEM_COLS_NO_EMBED`: explicit 19-column SELECT excluding embedding blob at all batch `id IN` fetch sites (5 sites) — reduces I/O on 8k+ memory DBs.
- `_mem_cache`: in-process dict cache; genesis types (ROOT/CP/ID) cached permanently; others TTL=60s; patched all 5 id IN batch fetch sites.

**Knowledge retrieval pipeline designed (#255)**: graph → web → LLM synthesis → deposit. Filed; not yet implemented.

**Filed**: #256 Tailscale remote access; #257 needs-Designer async design channel.

*Updated: 2026-03-15f by Claude Code (Scribe).*

---

### Session 2026-03-15g additions (slow query whack-a-mole + MemoryStore epic; worker bug burned credits)

**G-QP3 ~~CLOSED~~**: `cortex.get_by_type()` used `SELECT *` for EPISODIC/FACTUAL boot scans — loaded embedding blob on every type scan (332ms + 63ms at boot). Fix: `SELECT {_MEM_COLS_NO_EMBED}` in `get_by_type()`; same fix in `consolidation.py` + corrected `ORDER BY created_at → timestamp`. Issue #259.

**G-QP4 ~~CLOSED~~**: `cortex.get_habits()` called per-turn; each call did full-table `LIKE` metadata scan → 55ms × multiple hits per turn. Fix: `_habit_cache` (Optional[list]) on Cortex; populated on first `get_habits()` call; invalidated by `store()` when `is_habit=True`; cache persists session lifetime. Issue #260.

**G-QP5 ~~CLOSED~~**: `meaning_to_me` layer `UPDATE` ran on every restart (80ms LIKE scan; no migration guard). Fix: `_migrations` table added in `_init_db()`; `meaning_to_me_layer_tag` marker prevents re-running — fires once, skipped thereafter. Issue #261.

**Worker integer bug fixed**: `PENDING` variable had trailing newline from `grep -c` output; `[ "$PENDING" -eq 0 ]` comparison treated newline-tainted value as non-zero → infinite loop; Worker kept spawning Claude instances burning ~$90 Anthropic credits. Fix: `tr -d '[:space:]'` strip on `PENDING` + defensive `2>/dev/null` on comparison. `claudecode/worker` updated.

**D091 — MemoryStore epic filed (#262)**: Consolidate all memory access concerns (cache, `_MEM_COLS_NO_EMBED`, boot scans, migration flags, habit trigger index) into a `MemoryStore` data layer; `Cortex` = reasoning layer only. Mirrors the `db_proxy`/`inference_gateway` architectural split. Children #259-261 done first; MemoryStore design next.

**G-SC1 urgency elevated**: D088 OR failover still not built. Worker bug burned ~$90 Anthropic credits in one session — failover is now high-priority. Build D088 FIRST next session before any other work.

---

### Session 2026-03-15h additions (cost control + performance foundation; D088 done; D092 designed)

**G-SC1 ~~CLOSED~~**: D088 fully implemented. `superclaude` rewritten: sources `.env`, reads `anthropic_balance.json` (24h TTL), falls over to OR (`ANTHROPIC_BASE_URL=https://openrouter.ai/api`) when balance ≤ $10; logs every decision + balance to `~/.TheIgors/logs/superclaude.log`. `check_claude_balance` Igor tool added to `browser.py` — scrapes `console.anthropic.com/settings/billing` using employer Chrome profile, parses balance, writes `{balance_usd, fetched_at}` to `~/.TheIgors/cc_channel/anthropic_balance.json`.

**G-DB1 — db_proxy universal gateway (D092, #263)**: `db_proxy` becomes the universal storage gateway for ALL databases (memories, notebook, budget, word_graph). W1: no raw `sqlite3.connect()` anywhere — every DB goes through a `DatabaseProxy` instance. W2: `ensure_index()` + EXPLAIN-based usage tracking + `_cc_index_registry` table. Foundation for LMDB migration (word/habit graph) without touching callers. In-progress (T-d092-proxy-w1w2).

*Updated: 2026-03-15h by Claude Code (Scribe).*

---

### Session 2026-03-15d additions (design + implementation sprint)

**New gaps discovered:**

**G-DSP1 — Dashboard display: Cloud%/cloud_mode contradiction + p95 outlier** *(S — display only)*
`Cloud: 0%` shown while `preparse skipped (cloud mode)` also shown — two different signals (mode gate vs call fraction) with no label distinction. p95=186,951ms caused by single Feb timeout still in n=20 rolling window. Fix: distinguish labels; cap window at 24h or exclude >60s outliers. Ticket: #247.

**G-RSP1 — Response quality: habit trace leak + knowledge query misrouting + Mashter in canned responses** *(S-M)*
'Habit executed. [BL_...]' leaking into user-facing response. 'What do you know about grammar?' triggering canned 'I don't know that one, Mashter' instead of LLM+memory. Character voice baked into canned response text firing on knowledge queries. Ticket: #248.

**Design decisions recorded (not gaps but load-bearing):**

- **Watchlist (#240)**: `habit_type="watch"` subtree — fires salience boost instead of action; named inspectable list; `watch_expires` in metadata; inward + outward facing entries.
- **BG meta-habits (#241)**: all BG rules should eventually be graph nodes, not Python. "Less code more data."
- **Executive function (#242)**: emerges from inter-layer inspection topology, not a module. PFC analog = dense bidirectional inspection edges.
- **Self-observation (#243)**: habit subtree firing on own output patterns; async NE-pattern; inward-facing watchlist entries.
- **Meaning-to-me cluster (#244)**: named node cluster between interpretive edges and CP/ID nodes; `metadata.layer=meaning_to_me`; threads traversing it get personally-significant flag.
- **Salience elevation (#245)**: distributed, no single owner — watchlist, NE, meaning-to-me, attractor all contribute independently.
- **Intrinsic motivation (#246)**: curiosity as idle state (low arousal + positive valence + open attractor); NE internal_state → milieu reward signal; temporal credit assignment ('thanks past self') deferred.

**G-WG1 — wg_cooccur INSERT contention (SQLite word graph)** *(S)*
`INSERT INTO wg_cooccur` hitting 1000-4000ms. Word graph uses its own SQLite DB (DatabaseProxy, not PGDatabaseProxy) — contention when multiple turns write co-occurrence data simultaneously. Fix candidates: (1) WAL mode on word graph DB, (2) batch inserts, (3) migrate wg_cooccur to Postgres. Classification: SQLite write-lock limit (not a bad query). Observed: 2026-03-17.

**G-WIN1 — Windows box boot: 4 blocking bugs** ~~*(S)*~~
**RESOLVED 2026-03-20d** — Windows instance `igor_wild_windows_0001` failed to boot due to four distinct bugs:
1. `UnicodeEncodeError` (Rich box-drawing chars on CP1252 console) → `igor_loop.ps1`: added `PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8`.
2. `UndefinedTable: relation "memories" does not exist` (fresh Postgres, no schema) → `cortex.py`: added `_PG_SCHEMA` DDL constant (13 tables) + `_init_pg_schema()` + `_init_db()` PG try/except.
3. `INTEGRITY_CHECK FAILED — MISSING: CP1-CP6` (genesis skipped) → `core_patterns.py`: genesis guard changed from `total_count() > 0` to `cortex.get("ROOT") is not None`; root cause: `boot_env_sync` writes SYSCFG_* memories before `initialize_genesis`, making count > 0.
4. `memory_sync psycopg2 errors` → `tools/memory_sync.py`: fixed `_pg_connect` cursor_factory + `_UPSERT_SQL` VALUES `%s` placeholder.
Result: Igor boots clean on Windows — CP·6 ID·14 67 memories, INTEGRITY_CHECK PASS.

*Updated: 2026-03-20d by Claude Code.*

---

### Sessions 2026-03-16 through 2026-03-20g (consolidated update)

**Decisions closed / implemented:**

- **D163 — memory-sync-full-db-per-box ~~CLOSED D169~~**: T-memory-sync #293. Hub-and-spoke swarm sync — full Postgres replica per box; bidirectional via GREATEST(activation_count). `tools/memory_sync.py`: `sync_memories()` tool, PROC_MEMORY_SYNC habit every 6h, `full=true` bootstraps new box. Gate: `IGOR_SWARM_DB`.
- **D167 — traces-get-mcp ~~CLOSED~~**: `traces_get(trace_id)` MCP tool in igor_mcp.py — full ordered activation sequence for a trace.
- **D172 — mcp-igor-claudecode ~~CLOSED~~**: igor_mcp.py wired into `.claude/settings.json`; CC queries Igor DB directly via MCP without paste.
- **D173 — reading-integration-pipeline ~~CLOSED~~**: T-reading-integration #295. 5-step encoding pipeline (embed+link+spine+interp+arousal) in `tools/reading_integration.py` + `claudecode/reading_integrator.py` backfill. `_deposit_nodes()` is canonical deposit primitive. book_learner now runs pipeline inline.
- **D174 — cortex-tails-migration ~~CLOSED~~**: `ALTER TABLE tails ADD COLUMN trail_id/sequence_pos` must precede index creation — migration-before-index pattern established.
- **D177 — fork-context-propagation ~~CLOSED~~**: T-fork-primitive #297. Fork habit dispatches branch_habits[] with shared traversal_context via args dict. TWM approach rejected (no set_twm_key API).
- **D178 — habit-audit-pipeline ~~CLOSED~~**: Archived 995 habits (991 zero-activation BL_*, 3 pipeline suppressors, 2 dead-trigger). 124 active habits remain. PROC_DIRECTION_AWARE wired as context_inject/heartbeat_check; PROC_RESP_COMPLEX changed to context_inject.
- **D179 — reading-experiment-roadmap ~~defined~~**: 8-experiment roadmap: experiments 1-5 done; experiment 6 (bulk reading, 146 items) running; 7=swarm, 8=capacity.
- **D180 — pipeline-arch-resolved ~~CLOSED~~**: T-pipeline-arch resolved without code changes: preparse always skipped (IGOR_SKIP_PREPARSE_ON_CONFIDENT), OR contention phantom, drain runner path bug was the real blocker.
- **D181 — paths-default-fix ~~CLOSED~~**: `paths.py` default instance_id corrected Igor-wild-0001 → igor_wild_0001. Root path case bug affecting drain runner and internal path resolution.
- **D182 — scribe-pattern-retired ~~CLOSED~~**: Scribe worker pattern retired. Day-close is now manual-only. 15 pending scribe tasks cancelled. Savestate skill no longer auto-generates scribe queue items.

**New gaps / tickets:**

- **T-pipeline-arch** (pending): Inference pipeline review — preparse, cloud routing, NE redesign. Remaining: gap logging (M-size) + NE redesign (L-size, deferred post-experiment-7).
- **#297 T-fork-primitive** (OPEN on GitHub — verify if closed): unconditional multi-branch habit node.
- **#298 T-if-fork-primitive** (OPEN): conditional fork — branch fires when guard evaluates true.
- **#299 T-watchlist-habits** (OPEN): seed watch nodes for Akien's topics + executive function questions.
- **#300** (OPEN): Make foreground reading speed configurable — IGOR_READING_SPEED_SPS.
- **#289 T-trail-training** (OPEN): Hebbian edge strengthening from co-activation traces.
- **#288 T-graph-calving** (OPEN): Depth + attractor-divergence triggered tree splitting.

**Trails infrastructure ~~CLOSED~~**: T-trails-infra. `tails` table (node_id, weight, recorded_at, trail_id, sequence_pos). `cortex.trails_through_node()`, `cortex.trail_gradient()`, `cortex.hot_paths()`. `inspect_trail` + `trail_hot_paths` tools in `tools/trail_inspector.py`. MCP: tail_heat, traces_recent, traces_get, hot_nodes.

*Updated: 2026-03-20g by Claude Code.*

---

### Session 2026-03-20g continuation — codebase audit

**Audit complete (run_review_audit.sh checklist, 10 checks):**

- **Check 10 — Exception hygiene (CLOSED)**: 284 bare-pass `except X: pass` blocks replaced with `logging.getLogger(__name__).warning()` calls across 46 files. Rule: NO BARE PASS ANYWHERE. Also fixed 9 files where transformation script broke `from __future__ import annotations` ordering.
- **Check 7 — Async timeouts (CLOSED)**: confluence.py: added `timeout=_CONFLUENCE_TIMEOUT` (30s, `IGOR_CONFLUENCE_TIMEOUT_S` env var) to all 8 HTTP calls. discord_bot.py: added `aiohttp.ClientTimeout(total=15)` to webhook POST.
- **Check 2 — Hardcoded values (CLOSED)**: browser.py: replaced hardcoded `"claude-haiku-4-5-20251001"` with `BROWSER_USE_ANTHROPIC_MODEL` env var.
- **Check 9 — Architecture drift (CLOSED)**: capabilities_index.dsb: added SECTION_GRAPH_OPS (3 tools), SECTION_OPS (4 tools), SECTION_WATCHLIST (1 tool), SECTION_SUDO_RELAY (1 tool); updated TOTALS to 148 tools, 10 env gates.

**New ticket opened:**
- **#303 T-igorbase-universal**: IgorBase as universal base class for all objects — emergency stderr fallback, module-level helper for tool files. Currently ~15 classes inherit it; goal is system-wide adoption.

*Updated: 2026-03-20g continuation by Claude Code.*

---

### Session 2026-03-21 — QA sweep (Claude Code)

**Tickets closed:**

- **#302 — wg_cooccur query timeouts ~~CLOSED~~**: G-WG4 implemented. `_pg_get_neighbors` word list capped at 20 (was unbounded, caused 160-545ms Postgres queries). `reinforce_text` token cap at 40 (prevents O(n²) pair explosion). VACUUM ANALYZE on 29M-row wg_cooccur table: baseline query 133ms → 82ms. G-WG1 (SQLite contention) is no longer active — table is now in Postgres.
- **#303 T-igorbase-universal ~~CLOSED (phase 1)~~**: `_EmergencySafeLogger` added to igor_base.py — falls back to sys.stderr on logging infra failure. `get_logger(name)` module factory for tool files. `IgorBase.log` property now returns _EmergencySafeLogger. Phase 2 (migrate 200+ bare-pass blocks) is separate effort.
- **#284 resource_manager.py ~~CLOSED (S scope)~~**: `tools/resource_manager.py` shim re-exports from budget.py. No callers changed. Long-term direction signal for new code.
- **#272 cortex SELECT * ~~CLOSED (partial)~~**: Eliminated 5 `SELECT * FROM memories` queries — all use `_MEM_COLS_NO_EMBED`. Prevents embedding blob inflation on Postgres wire transfers.
- **#271 font size UI ~~CLOSED~~**: A-/A+ buttons added to name-row. localStorage persistence.
- **#297 T-fork-primitive ~~CLOSED~~**: Was implemented in commit 0c24d9f (2026-03-20) but issue wasn't closed. Confirmed live-tested and working.

**G-WG1 update:** G-WG1 (wg_cooccur SQLite contention) is superseded by Postgres migration (D126). The active gap is now Postgres query latency — addressed by G-WG4 (#302 fix above).

**Skipped (architecture/design needed):**
- #295, #289, #308-310: L-size, need Akien design session
- #285-288: L-size infrastructure patterns, need design
- #299, #317-319: depend on #298 (if-fork) or L-size design
- #256: human steps required (Tailscale device setup)

*Updated: 2026-03-21 by Claude Code.*

---

### Session 2026-03-21b — Foreman loop + bug sweep

**Gaps closed:**

- **G-LOG1 ~~CLOSED~~**: `log_error` not imported at module level in `inference_gateway.py`, `ollama_reasoner.py`, `push_sources.py` (openrouter_reasoner.py fixed prior session). Every except handler that called `log_error` would itself raise `NameError`, masking the original error. Fixed: module-level `from .forensic_logger import log_error` added to all three files; redundant local imports removed.

**New gaps (open):**

- **G-HAB-TRIGGER1** (open): Habit trigger matching is pure substring scan — any input containing a trigger word fires the habit regardless of intent. Causes misfires (wrong habit fires) and loop halts (bad habit terminates turn). D201 proposed: structured preparse conditions `{intent, entities, complexity}` matched against thalamus output instead of raw text. Timeout watchdog (habit execution hard timeout → loop continues) proposed as independent floor. Igor designed both; tickets pending from session 2026-03-21b.

---

### Session 2026-03-21d — Bug sweep

**Gaps closed:**

- **G-LOG2 ~~CLOSED~~**: `log_error` not imported at module level in `ebook_reader.py` — same class of bug as G-LOG1 but missed in that sweep. Used throughout for exception handling but never imported; every error path would itself raise `NameError`, masking the original error. Fixed: `from ..cognition.forensic_logger import log_error` added to imports. Igor filed #329 while fix was being shipped; closed immediately.

- **G-DB-PROXY1 ~~CLOSED~~**: db_proxy does blanket `sql.replace("?", "%s")` for psycopg2 parameter translation. PostgreSQL's jsonb key-exists operator is also `?` (e.g., `metadata ? 'trigger'`), so it was incorrectly translated to a parameter placeholder with no corresponding parameter → `IndexError: tuple index out of range` on every boot. Root cause: GIN index optimization in `get_habits()` switched from `jsonb_exists(metadata, 'trigger')` to `metadata ? 'trigger'` without accounting for the blanket translation. Fixed by reverting to `jsonb_exists()` form which is unambiguous.

- **G-QP6 ~~CLOSED~~**: `cortex.search()` supplement scan fetched up to 300 wide rows (`ORDER BY activation_count DESC LIMIT 300`) on every call to cover orphan nodes not reached by traversal. With 11k memories and depth=3 BFS from 21 roots (CP1-CP6 + ID1-ID14), traversal already reaches 80+ nodes — supplement was redundant for all normal queries and caused 500ms slow queries on every NE cycle (~60s). Fix: skip supplement when `len(_traversal_pool) >= _SUPPLEMENT_THRESHOLD` (80). Supplement still fires for sparse graphs (new instances, shallow traversals).

*Updated: 2026-03-21d by Claude Code.*

---

### Session 2026-03-21e+f — Worker orchestration + Hebbian training

**Gaps closed:**

- **G-NE-LOOP1 ~~CLOSED~~**: NE consolidation loop ran indefinitely after completing a pass. Root cause: `_deep_consolidation_pass()` set `_consolidation_running = False` but never updated `_last_consolidation_ts`, so `is_consolidation_eligible()` immediately re-qualified and launched another pass. Fix: set `self._last_consolidation_ts = time.monotonic()` at end of pass; add check in `is_consolidation_eligible()` that blocks re-run until another full idle period. Pushed 0694d6d; activated on Igor restart 2026-03-22.

- **G-WORKER-INJECT1 ~~CLOSED~~**: xdotool-based worker orchestration was fragile — required X display, precise timing (sleep 0.3s between type and Return), and the injection chain depended on Igor's PROC_WORKER_FOREMAN habit (which was never seeded in the live DB). Workers frequently got stuck mid-queue. Fix: replaced with `worker_daemon.sh` — bash loop that polls queue every 20s, runs `claude --dangerously-skip-permissions "/sprint <id>"` for each pending ticket as a fresh process, self-chains without Igor or xdotool. cc_queue.py `worker-launch` now just ensures the daemon is running. Sprint skill Step 4 simplified accordingly.

**New gaps (open):**

- **G-WIN1** (open): `reading_integrator.py` crashes on Windows (exit 1, traceback at line 423). Likely path separator or dependency issue on Windows Python. Ticket: T-reading-integrator-windows (S-size, in queue).

*Updated: 2026-03-22 by Claude Code.*

---

### Session 2026-03-21g — Design sprint (post-Akien signoff)

**Gaps closed:** none (design-only session)

**Design docs produced:**

- `T-trails-infra.csb.txt`: DDL for trail_metadata + trail_activations tables; phantom tails migration fix (ALTER TABLE for missing trail_id/sequence_pos); TWM→trail join via twm_obs_id; three temporal systems (milieu/TWM/tails) unified view. Pending Akien approval before worker.
- `T-interoception.csb.txt` (companion to D336): ResourceMonitorSource continuous VAD gradient; alpha_override=0.05; 3-min rolling window. Pending Akien approval.
- `T-inference-colocation-signal.csb.txt`: Ollama+DB colocation detection; soft routing penalty when colocated+CPU>70%; IGOR_COLOCATION_AWARE gate. S-size.
- `issue-308.csb.txt`: WG memory bridge — WG predictions seed Phase1 candidates; NE promotions train WG; IGOR_WG_SEARCH_SEEDING gate. L-size, design-first.
- `issue-334.csb.txt`: IgorBase universal logging — manual log_step at semantic decision points; ring_memory primary sink; decorator overhead benchmark required. L-size.
- `issue-335.csb.txt`: start_at field on memories — temporal anchoring distinct from storage timestamp; HIGH-inertia touch on models.py requires Akien review. L/XL-size.

**Queue additions:** T-test-debt-tooling (S) — tests for session_manager.py + decision_manager.py.

*Updated: 2026-03-22 by Claude Code.*
