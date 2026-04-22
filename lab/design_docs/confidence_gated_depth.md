---
title: Confidence-gated depth — per-stage inventory and scoping
ticket: T-confidence-gated-depth-scoping
decision: D-preparse-architecture-2026-04-22
date: 2026-04-22
status: design-only
---

# Confidence-gated depth — per-stage inventory

## Principle (from D-preparse-architecture)

Every cognitive stage emits a **confidence score**. The next stage is
gated on that score: **high confidence → short-circuit; low confidence
→ proceed to full processing**.

This is a principle, not a single file change. Each stage has its own
"what does confidence mean here?" question and its own "what's the
short-circuit do?" answer. This doc inventories the nine stages, notes
where confidence is already emitted vs missing, and proposes concrete
per-stage tickets.

The nine-stage model (from the conversation 2026-04-22):

```
attend → predict → recognize → retrieve → reason → select → articulate → reflect → learn
```

---

## Stage-by-stage inventory

### 1. attend

**What it does:** decides whether this stimulus deserves processing.
Input-gate for the pipeline. Currently: every non-empty input gets
attended to; impulse-turns skip some pipeline branches, but there's no
"ignore this, it's noise" gate.

**Confidence emission today:** none.

**What confidence would mean here:** "is this stimulus worth spending
pipeline cycles on?" Low confidence = probable noise (accidental
keypresses, backscatter from another conversation, single-word fragments
with no context). High confidence = clearly directed-at-Igor content.

**Gating:** low confidence → drop or log-only; high confidence → enter
pipeline.

**Risk of building this:** Igor could filter out genuine input that
happens to look noisy. Start with log-only (observe what would have
been filtered) before enabling the actual drop.

**Proposed ticket:** `T-attend-confidence-score` (S) — add a salience
score to the attend stage, emit it, log-only mode first.

---

### 2. predict

**What it does:** NE (neural entrainment) forms a prior over what's
about to come in — predicted habits, predicted search keys. Before
input arrives, predict what you'll see.

**Confidence emission today:** `_ne_pred.predicted_search_keys` gives
a list, but no confidence score. `ne.record_actual()` measures surprise
post-hoc but that's a learning signal, not a gating signal.

**What confidence would mean here:** "how strongly does NE predict the
incoming shape?" Low confidence = neutral prior, accept whatever
comes. High confidence = strong expectation, primes downstream stages
(memory search keys pre-warmed, likely habits pre-fetched).

**Gating:** high confidence prediction that *matches* actual input →
short-circuit recognition stage (we already know what it is). Low
confidence OR mismatch → proceed to recognize.

**Risk:** confirmation bias — NE predicts greeting, Igor classifies as
greeting even when input is actually a question phrased similarly.
Mitigate with a lightweight sanity check ("does the input have a
question mark? does it have an action verb?") before accepting the
short-circuit.

**Proposed ticket:** `T-ne-predict-confidence-gate` (M) — NE emits a
prediction_confidence, recognize stage short-circuits when
confidence ≥ threshold AND input-shape sanity check passes.

---

### 3. recognize

**What it does:** classify the input — intent, complexity, entities.
Today: `basal_ganglia.select_habit()` returns `(habit, confidence,
near_misses)`. Thalamus complexity classifier also runs.

**Confidence emission today:** **YES** — `_thalamus_confidence` is
already emitted and used by `T-gist-before-retrieve` to gate
cortex.search. This stage is the most mature of the nine.

**What confidence would mean here:** already well-defined — BG habit-
match score in [0,1].

**Gating:** already implemented in T-gist-before-retrieve — high
confidence + reflex intent → skip cortex.search.

**Extension:** extend reflex-skip set beyond `greeting` → `meta_question`
(self-referential, doesn't need episodic memory), `ack` / `farewell`
(if they become distinct classifications).

**Proposed ticket:** `T-recognize-reflex-set-extension` (S) — extend
`_REFLEX_INTENTS` in `gist_gate.py` and study impact over a few days
of real traffic.

---

### 4. retrieve

**What it does:** cortex.search — pull episodic memory candidates for
the turn. Returns ranked list.

**Confidence emission today:** candidates are scored (cosine similarity,
recency, salience), but no aggregate "how good is this retrieval?"
signal.

**What confidence would mean here:** "did memory search find relevant
context, or is this a cold look-up?" Low confidence = no close matches,
retrieval adds no value. High confidence = clear relevant candidates.

**Gating:** low confidence → drop candidates, don't let noise dilute
reasoning context. Today they get included regardless of quality.

**Risk:** discarding weak-but-valid memory that could still inform the
answer. Mitigate with a confidence *floor* rather than a cutoff — keep
top-K always, tag low-confidence ones as "weak match" for downstream.

**Proposed ticket:** `T-retrieve-confidence-floor` (S) — emit
retrieval_confidence from cortex.search, tag weak candidates, never
drop below configurable floor (default keep top-3 regardless).

---

### 5. reason

**What it does:** the core inference step — LLM reasoning, tutor consult,
habit execution. Generates a draft response or plan.

**Confidence emission today:** tier-routing uses complexity as a proxy;
LLM reasoner doesn't emit a self-confidence score.

**What confidence would mean here:** "how sure is Igor about this
reasoning?" HARD — self-evaluated confidence from an LLM is
notoriously unreliable. Better approach: *divergence* from the shadow-
path (see T-shadow-stream-reasoning) is a stronger signal than self-
report.

**Gating:** low confidence → escalate to upstream tutor (T-tutor-not-
oracle-prompt). Today escalation is tier-based, not confidence-based.

**Risk:** HARD. Reasoning is the stage where LLM assistance is most
valuable and where graph-tree replacement is furthest off. Don't try
to replace this with trees yet.

**Proposed ticket:** `T-reason-divergence-confidence` (M) — compute
confidence from shadow-stream divergence rather than self-report;
gate tutor-escalation on the divergence signal.

---

### 6. select

**What it does:** picks the response form — do we reply, stay silent,
ask a question, emit a fragment? Reflex greeting, detailed explanation,
acknowledgment-only, etc.

**Confidence emission today:** reply-vs-silent gates exist (backchannel
thresholds, bare-ack suppression, reflex-reply paths) but no unified
confidence on the selection.

**What confidence would mean here:** "is this the right response
*shape*?" High confidence → commit to form. Low confidence → fall back
to safe default (neutral acknowledgment, or stay silent if below
floor).

**Gating:** low confidence on selection → use a conservative default
form ("got it" or equivalent) rather than a possibly-wrong detailed
reply.

**Risk:** over-defaulting to bare-ack regresses the conversational
quality. Keep form-selection confident unless clear signal otherwise.

**Proposed ticket:** `T-select-form-confidence` (M) — unify the
scattered reply-shape decisions into a single form-selection stage
with emitted confidence; conservative fallback when low.

---

### 7. articulate

**What it does:** produce the actual output text from the selected
form. Voice stage — character coherence, register, register-appropriate
humor level.

**Confidence emission today:** no unified score; DecisionBlob has a
`confidence` field that feeds voice_context but it's carried through,
not emitted by articulate itself.

**What confidence would mean here:** "did the articulation land as
intended?" Hard to self-evaluate pre-emission. A post-emission signal
(user response shape, engagement, did-they-come-back) is more reliable.

**Gating:** none at emission time. Post-emission: low-confidence
articulations feed the shadow-stream divergence corpus for later
learning.

**Proposed ticket:** `T-articulate-post-emission-signal` (M) — capture
post-reply user-response shape as an articulation-quality signal for
shadow-stream learning. Not a gate; a learning signal.

---

### 8. reflect

**What it does:** post-turn self-assessment — what worked, what didn't,
what to learn from this turn.

**Confidence emission today:** Pursuit evaluate_completion emits
completion/abandonment dopamine. Partial coverage; not unified.

**What confidence would mean here:** "how confident is Igor that this
turn went well?" Used for: update of habit weights, spawn of
corrective pursuits, log flagging for later review.

**Gating:** low reflection confidence → flag the turn for tutor review
(T-tutor-not-oracle-prompt) during idle time. High → incorporate
normally into learning.

**Proposed ticket:** `T-reflect-turn-confidence` (M) — unified reflect
stage with confidence; low-confidence turns go into review queue for
idle-time tutor consultation.

---

### 9. learn

**What it does:** update weights, form new habits, store new memories.

**Confidence emission today:** memory writes happen, BG habit weights
get updated, no unified learning-confidence.

**What confidence would mean here:** "how much should this turn
influence Igor's priors?" High confidence → strong update. Low
confidence (e.g., turn that Igor himself is unsure about) → small
update, wait for reinforcement.

**Gating:** low confidence → keep the lesson tentative (tag memory as
provisional, don't strongly weight the habit update until replay
confirms). High confidence → commit.

**Proposed ticket:** `T-learn-update-magnitude-by-confidence` (M) —
scale weight updates and memory salience by reflect-stage confidence;
provisional tag for low-confidence memories.

---

## Aggregate proposed tickets (9 stages)

| Ticket | Size | Priority notes |
|---|---|---|
| T-attend-confidence-score | S | Low-risk, log-only first |
| T-ne-predict-confidence-gate | M | Pairs well with existing T-gist-before-retrieve |
| T-recognize-reflex-set-extension | S | Incremental over shipped T-gist-before-retrieve |
| T-retrieve-confidence-floor | S | Cortex.search API extension |
| T-reason-divergence-confidence | M | Depends on T-shadow-stream-reasoning landing |
| T-select-form-confidence | M | Biggest unification work |
| T-articulate-post-emission-signal | M | Cross-turn signal capture |
| T-reflect-turn-confidence | M | Pursuit-aware |
| T-learn-update-magnitude-by-confidence | M | Depends on reflect confidence |

Total: 3× S, 6× M. These are NOT filed as tickets yet — this doc IS
the scoping deliverable for T-confidence-gated-depth-scoping. Akien
reviews this doc and decides which per-stage tickets to file,
whether to reshape any proposals, and the sprint order.

---

## Threshold-tuning approach (generic)

Each per-stage ticket will need a confidence threshold to decide the
gating behavior. Proposed convention:

- **Default threshold**: 0.7 (conservative; matches
  `IGOR_GIST_CONFIDENCE_THRESHOLD` default in gist_gate).
- **Per-stage env var**: `IGOR_CONF_<STAGE>_THRESHOLD`, e.g.
  `IGOR_CONF_ATTEND_THRESHOLD`, `IGOR_CONF_RETRIEVE_THRESHOLD`.
- **Observation-first rollout**: every new stage ships log-only
  initially. Only flip to active gating after a week of observed
  data shows the gate fires sensibly.
- **Two-knob tuning**: the threshold AND the min-observations-before-
  gate-fires count, so cold-start doesn't wreak havoc.

---

## Non-goals for this doc

- Deciding implementation details per stage — each child ticket will
  do that at sprint time.
- Threshold values — proposed default is 0.7, real values come from
  observation.
- Whether all 9 stages get built — some may remain unchanged if cost/
  benefit doesn't justify the work.

## Next step

Akien reviews this doc. Per-stage tickets get filed from the Aggregate
table above (wholesale or selectively). Shipped tickets become children
of D-preparse-architecture-2026-04-22 like their siblings; each child
ticket inherits the blanket HIGH-inertia pre-approval already recorded
on that decision for any main.py or pipeline touches.
