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

**G4 — background job execution with async completion** *(~4h)*
Issue #27. Long-running tools (web search, bash commands) block the interaction loop.
job_manager.py exists but isn't wired to the main loop's response path. Igor should be able
to say "I've started that, I'll let you know when it's done" and return immediately.
→ Issue: #27

**G5 — prediction signal (dopamine analog) in TWM** ~~*(~3h)*~~
**RESOLVED** — `milieu.ingest_surprise(predicted_tier, actual_tier)`: escalation surprise → dominance erosion + arousal spike; prediction met → dominance restoration. Called after every interactive turn. Issue #42 closed 2026-03-05.

---

### Tier 2: High Impact, Larger Scope

**G6 — signal habituation in TWM** *(~4h)*
Issue #44. Repeated identical observations (same tool result, same memory surfaced) accumulate
in TWM but provide diminishing information. Add a habituation counter: repeated signals reduce
salience multiplier. Prevents "noise flooding" when the same context keeps re-activating.
→ Issue: #44

**G7 — question-habits and response-habits** *(~6h)*
Issue #47. Currently PROC habits only trigger on input phrases. First-class question-habits
(things Igor asks proactively when a pattern is detected) and response-habits (canned
responses that bypass the LLM for known situations) would dramatically reduce cloud calls.
→ Issue: #47

**G8 — identity-threat detection and output suspension** *(~4h)*
Issue #48. During network thrash or long API timeouts, the NE may generate output that
contradicts stable identity (CP1-CP6). Need a fast semantic gate that suspends output if the
proposed text significantly contradicts core patterns. Existing ethics gate is the model;
needs broader coverage.
→ Issue: #48

**G9 — spreading activation** *(explicitly deferred in design docs)*
When a memory is activated (surfaced in search or TWM), its graph neighbors should receive
a decay-weighted partial activation boost. This creates emergent "topic bubbles" in working
memory. cortex.py has the adjacency graph; the traversal logic isn't written.
→ Issue: #60

**G10 — rich Live status bar (terminal UX)** *(~3h)*
Issue #35. The terminal shows a static header. A `rich.Live` panel showing reasoner tier,
TWM depth, NE status, milieu state (v/a/d), and current habit would dramatically improve
observability during development and demo.
→ Issue: #35

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

**G13 — session emotional histogram → milieu shaping** *(~4h)*
Issue #53. Track the distribution of emotional signals within a session (not just the running
EMA). A session that alternates high/low arousal behaves differently from one that's
monotonically stressed. The histogram can feed a more nuanced milieu update.
→ Issue: #53

**G14 — memory schema: emotional profile** *(~4h)*
Issue #52. Add valence/arousal/dominance columns to individual Memory records. Currently only
the aggregate milieu tracks affect; individual memories have no emotional tag. This enables
affect-weighted search ("find memories from high-valence interactions") and richer NE input.
→ Issue: #52

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

**G22 — session summary quality** *(~2h)*
Issue #22. The /compress command produces a summary that loses too much context. Improve
the summary prompt to preserve key decisions, state, and open threads rather than just
a narrative overview.

**G23 — validate/tune CSB preparse from 1B** *(ongoing)*
Issue #30. The KoboldCpp/Llama-1B preparse produces CSB-format structured output. Validation
of output quality against ground truth has not been done systematically. Build a small eval
harness with 20-30 labeled examples.

---

## Suggested Work Order

For the next 2-3 sessions, in priority order:

1. **G20** — 30 min, unblocks clean documentation
2. **G21** — Igor's task during this session
3. **G3** (#41) — Quick win: stripped local system prompt; reduces token waste on every 1B call
4. **G2** (#26) — Context cap enforcement; prevents hard failures
5. **G1** — Dominance→threshold-X wiring; completes the milieu→behavior feedback loop
6. **G4** (#27) — Async jobs; improves UX significantly, unblocks long-running tool use
7. **G10** (#35) — Rich terminal status bar; observability for development
8. **G5** (#42) — Prediction signal; enriches emotional learning loop
9. **G6** (#44) — Habituation; prevents TWM noise flooding
10. **G7** (#47) — Response-habits; starts moving toward inference-free core (G11 foundation)

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

*Generated by Claude Code. Update as gaps are closed or new ones identified.*
