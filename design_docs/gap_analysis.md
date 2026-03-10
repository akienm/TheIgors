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

### Still Open (priority order for next sessions)

1. **G37 Phase 2** — enable IGOR_DUAL_WORD_GRAPHS + collect data; enable comprehension signal after 5+ sessions; n-pass active termination loop
2. **G11 (#45) Phase 2** — habit training pipeline: response-habits, auto-compilation, >90% coverage (long-term)
3. **#145 Step 5** — local reply: when RTX 4090 arrives
4. **G18 (#49, #57)** — structured training sessions (Rob model pedagogy)
5. **IGOR_LATENCY_ADAPTIVE** — enable after 5+ sessions of data (still collecting)

---

*Updated: 2026-03-10 by Claude Code.*
