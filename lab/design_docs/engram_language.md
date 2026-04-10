# Engram Language Specification

*Decision D208. Last updated 2026-03-23.*

---

## 1. Name and Etymology

**Engram** — named by Igor, 2026-03-22.

From Richard Semon, *Die Mneme* (1904): the *engram* is the physical trace that an experience leaves in neural tissue. Not a pointer to memory, not a representation of memory — the literal substrate change that **is** the stored information.

> "You don't write code that runs separately from memory. You lay down engram nodes — template macros — that *become* the substrate. The engram IS the program."

The name is precise, not decorative. In Engram:

- A habit is an engram. It does not *refer* to behavior — it *is* the behavior, encoded in the graph.
- A template is a proto-engram: a parameterized node that expands into engrams at seed time.
- At runtime there is no interpreter, no call stack, no evaluation loop. There is only activation spreading through engrams.

---

## 2. Core Paradigm

Engram is a **reactive, graph-structured, template-macro language for the Igor matrix layer**.

| Property | Engram | Contrast |
|---|---|---|
| Execution model | Lateral inhibition (BLOOM_INHIBIT) | No scheduler, no call stack |
| Abstraction unit | Template macro | Not subroutine, not class |
| Code and data | Same nodes (Memory records) | Not separate |
| Control flow | Gradients + thresholds | Not boolean branches |
| Side effects | TWM pushes, cortex writes | Not file I/O or global state |
| Concurrency | Async by default | Not thread spawning |
| Self-modification | Template instantiation | Not reflection/eval |
| Closest ancestors | Lisp macros, Hebb's rule, dataflow | Not von Neumann, not OOP |

### BLOOM_INHIBIT: the execution model

Engram has no scheduler. When multiple habits could fire, they activate simultaneously and laterally inhibit each other. Whichever reaches threshold first suppresses the alternatives. BLOOM_INHIBIT is not a *pattern in* the execution model — it **is** the execution model. CONDITION_GATE and THRESHOLD_ALERT are named regions of the same inhibitory landscape.

> Igor: "At runtime, competing engrams fire simultaneously and laterally inhibit each other — whichever reaches threshold first suppresses the alternatives. There's no scheduler arbitrating between them. The competition *is* the execution."

### DISTILLATION: the compiler pass

Without DISTILLATION, the matrix accretes — remembers everything, therefore knows nothing, because retrieval cost grows with undifferentiated mass. DISTILLATION removes degrees of freedom while preserving signal. It is the only pattern that compresses rather than grows.

> Igor: "If the engram IS the program, then a bloated, undercompressed engram is a bloated, unrunnable program. DISTILLATION is the compiler pass that makes it executable."

---

## 3. Grammar

An Engram program is a set of **Memory nodes** (type PROCEDURAL or TEMPLATE) stored in the cortex graph.

### Habit node (atomic engram)

```
HABIT {
  id:          string           // unique, e.g. "PROC_GREET_MORNING"
  trigger:     string           // BG scorer pattern, or empty for condition-only
  conditions:  ConditionSpec    // structured metadata conditions (D201)
  action:      ActionSpec       // what fires on match
  metadata:    {
    habit_type: threshold | action | workflow | delegation | reactive
               | response | question | context_inject | cognitive
               | tool | passive_capture
    priority:   float           // BG score modifier
    inertia:     float          // 0.0–1.0; resistance to edit/deletion
    tags:        list[str]      // labels for search and inhibition
  }
}
```

### Template node (proto-engram)

```
TEMPLATE {
  id:            string         // e.g. "tpl-wonder"
  memory_type:   PROCEDURAL
  metadata: {
    schema_version: 1
    template: true              // BG executor guard: never fire directly
    slot_manifest: {
      slot_name: {
        type_hint: str|int|float|bool
        required:  bool
        default:   any
        validator: { min, max, pattern, choices, ... }
      }
    }
    expansion_schema: [         // list of habit dicts, Jinja2 templated
      { id: "{{prefix}}_TRIGGER", trigger: "{{keyword}}", ... },
      ...
    ]
    instantiation_contract: {
      produces:            list[str]   // habit IDs this expands to
      condition_signature: dict        // expected conditions on produced habits
      invariants:          list[str]   // postconditions in plain English
      edge_policy:         str         // "none" | "link_to_parent" | ...
    }
  }
}
```

### Condition specification (D201)

```
ConditionSpec {
  intent:          string          // "question" | "request" | "greeting" | ...
  tone:            string          // "urgent" | "casual" | ...
  min_complexity:  int             // 1–10
  max_complexity:  int
  tags:            list[str]       // has_ticket | has_code | multi_turn | ...
  keywords:        list[str]       // substring matches in input
  not_intent:      string          // exclude when intent equals this
}
```

Specificity bonus: +0.08 per matched condition field added to BG score.

### Action specification

```
ActionSpec {
  habit_type: "response" | "context_inject" | "tool" | "workflow" | ...
  response:   string              // for response habits: literal or template string
  tools:      list[str]           // tool IDs to call in sequence
  twm_push:   { key, value, ttl } // side-write to working memory
  delegate:   { target, args }    // for delegation habits
}
```

---

## 4. Primitive Operations (D204)

The primitive layer provides atomic ops callable from habit actions.

### Graph primitives
| Primitive | Description |
|---|---|
| `prim_node_create` | Create/upsert a Memory node in cortex |
| `prim_node_link` | Add a directed edge between two nodes |
| `prim_node_search` | Keyword + cosine search, returns top-N nodes |

### TWM (working memory) primitives
| Primitive | Description |
|---|---|
| `prim_twm_push` | Push observation to TWM with TTL |
| `prim_twm_read` | Read current TWM contents by key/pattern |

### String primitives
| Primitive | Description |
|---|---|
| `prim_str_split` | Split string by delimiter |
| `prim_str_regex` | Regex match/extract |
| `prim_str_format` | Jinja2 format string against context dict |
| `prim_str_slice` | Substring by index range |

### List primitives
| Primitive | Description |
|---|---|
| `prim_list_push` | Append to a named list in working context |
| `prim_list_pop` | Pop from front of named list |
| `prim_list_count` | Count items in named list |

---

## 5. Pattern Inventory (21 patterns)

Patterns are reusable template structures. Each names a recurring idiom in the habit graph.

---

### Original 10

**WONDER**
*Periodic curiosity probe — fire at interval, search cortex for something to surface.*
```
tick → search(TWM.recent_topics) → score salience → if salience > threshold: surface → push to TWM
```

**FILE_ITERATOR**
*Walk a sequence of items within a session, processing one per activation.*
```
trigger → load_cursor → get_next(cursor) → process(item) → save_cursor → loop
```

**THRESHOLD_ALERT**
*Accumulate signal; fire when count/value crosses threshold; reset.*
```
event → increment_counter → if counter >= threshold: fire_action → reset_counter
```

**SCHEDULER_TICK**
*Time-driven heartbeat. Wakes on interval, checks condition, acts.*
```
heartbeat → check_condition → if condition: execute_action → update_last_fired
```

**READER_LOOP**
*Consume a text source sentence-by-sentence, depositing nodes.*
```
open_source → loop: read_chunk → extract_nodes → deposit → advance_cursor → until EOF
```

**MEMORY_DEPOSIT**
*Transform an observation into a Memory node and store it.*
```
observation → classify_type → build_node(narrative, type, metadata) → cortex.store → return node_id
```

**SEARCH_AND_RESPOND**
*Retrieve relevant nodes, synthesize, reply.*
```
trigger → prim_node_search(query) → rank → build_context → generate_response → send
```

**CONDITION_GATE**
*Binary branch: only proceed if condition true; else no-op or alternate.*
```
trigger → evaluate_condition → if true: proceed_habits → else: (halt | alternate_habits)
```

**ERROR_RECOVERY**
*Try primary action; on failure: classify error, apply recovery strategy, retry or escalate.*
```
attempt_action → on_error: classify → if retryable: backoff → retry → else: escalate
```

**ASYNC_DELEGATE**
*Fan out to a subordinate process via TWM; decouple trigger from completion.*
```
trigger → push_task(TWM, target_habit, args) → continue_main → [target_habit fires separately]
```

---

### Igor's 10 additions (2026-03-22)

**ESCALATION_LADDER**
*Try cheapest resource first; escalate on failure. Distinct from ERROR_RECOVERY: this is pre-failure routing, not post-failure repair.*
```
attempt tier.1 → if fail: attempt tier.2 → if fail: attempt tier.3 → if all fail: ERROR_RECOVERY
```
*Canonical instance: inference gateway tier ladder.*

**CURSOR_RESUME**
*Batch-with-checkpoint across restarts. Distinct from FILE_ITERATOR: persists the cursor across sessions, not just within one.*
```
load_checkpoint → process_batch(checkpoint.offset) → save_cursor → if complete: done; else halt
```
*Canonical instance: book_learner, drain_learn_queue.*

**BLOOM_INHIBIT**
*All candidates activate; lateral inhibition; winner suppresses losers. This IS the execution model, not a pattern on top of it.*
```
candidates activate simultaneously → score_all → lateral_inhibit(losers) → winner fires → losers suppressed
```
*Note: CONDITION_GATE and THRESHOLD_ALERT are named regions of this landscape.*

**PREDICTION_CORRECTION**
*Predict, observe, compute delta, update weights. The learning loop embedded in execution.*
```
predict(next_state) → observe(actual_state) → delta = actual - predicted → update_weights(edges, delta)
```
*Canonical instance: NE anticipation pull, prospective/actual comparison.*

**DISTILLATION**
*Cluster episodic nodes, extract shared pattern, deposit one higher-type node, suppress originals.*
```
search(EPISODIC, query) → cluster(k=N) → extract_centroid → deposit(INTERPRETIVE|PROCEDURAL) → mark_originals_compressed
```
*Most critical missing pattern. The only one that compresses rather than grows. Without it: matrix accretes but doesn't learn.*

**SIGNAL_DEBOUNCE**
*Fire only if signal persists for N cycles. Prevents noise spikes from triggering.*
```
signal → set_pending_flag(TTL=N) → heartbeat → if flag still set: fire → clear_flag → cooldown(M)
```
*Canonical instance: NE interruptors, arousal spike guards.*

**PRIMING**
*Activate A → pre-weight related nodes → time window → decay. Anticipatory, not reactive.*
```
trigger_A → raise_edge_weights(related_to_A, boost=δ, ttl=T) → [decay naturally over T seconds]
```
*Canonical instance: NE anticipation — priming B before A's completion.*

**AFFECT_MODULATE**
*Read current milieu state → adjust thresholds across all downstream habits → return to baseline as milieu decays.*
```
milieu_read → for each habit: threshold *= (1 + arousal * sensitivity) → recalculate BG scores → apply
```
*Canonical instance: milieu as pervasive parameter; modulates everything.*

**REFRAME**
*Observe X → apply interpretive lens → produce new meaning → push modified observation.*
```
observe(X) → match_interpretive_edge(X, context) → apply_lens → deposit_reframed(X') → push(TWM, X')
```
*Canonical instance: NE affective frame selection; thalamus intent classification.*

**FANOUT_GATHER**
*Trigger N parallel delegations, wait for all, merge results, continue. Distinct from ASYNC_DELEGATE: this is synchronised fan-out.*
```
trigger → push_tasks([t1, t2, ..., tN]) → wait_all(results, timeout) → merge(results) → continue
```
*Canonical instance: swarm reading, multi-machine batch extraction.*

---

### Pattern #21: CACHED_PROBE (added 2026-03-23, Akien Maciain)

*Payload-configured data monitor. Dual invocation mode. Optional worry branch.*

```
trigger → check: age(cached_at) > cache_ttl?
  yes → cached_data = source.run(); update cached_at
  no  → skip fetch
if invocation == explicit:
  surface(cached_data)
if worry_after and age(cached_at) > worry_after:
  worry(cached_data)
```

**Payload slots:** `source` (fetch fn), `cache_ttl`, `worry_after` (optional), `cached_data`, `cached_at`.

Two invocation modes: `explicit` (always surface) / `heartbeat` (silent unless worry threshold crossed). Config lives entirely in the node — no separate evaluator. To create a monitor: write one memory node with those fields, attach this template. Replaces all bespoke resource monitor habits.

*Distinct from THRESHOLD_ALERT: THRESHOLD_ALERT counts up toward threshold; CACHED_PROBE decays by age — different axes.*

---

## 6. Example Programs

### Hello World — response habit
```
HABIT PROC_GREET_MORNING {
  trigger: "good morning"
  habit_type: response
  response: "Good morning. {{hour}} hours since last interaction. Milieu: {{milieu.valence:.2f}}."
}
```

### Escalation Ladder — inference routing
```
TEMPLATE tpl-escalation {
  slots: { prefix, tier1_habit, tier2_habit, tier3_habit }
  expands to:
    PROC_{{prefix}}_T1: try tier1_habit; on fail: push(TWM, "escalate_to_t2", ttl=30)
    PROC_{{prefix}}_T2: on TWM.escalate_to_t2: try tier2_habit; on fail: push(TWM, "escalate_to_t3", ttl=30)
    PROC_{{prefix}}_T3: on TWM.escalate_to_t3: try tier3_habit; on fail: PROC_ARBITER_ALERT
}
```

### Distillation pass
```
HABIT PROC_DISTILL_DAILY {
  trigger: scheduler_tick(interval=86400)
  habit_type: workflow
  tools: [
    prim_node_search(type=EPISODIC, min_count=10),
    prim_cluster(k=5),
    prim_node_create(type=INTERPRETIVE, narrative="{{cluster.centroid_narrative}}"),
    prim_node_link(source="{{new_node}}", targets="{{cluster.member_ids}}", edge="distilled_from"),
  ]
}
```

---

## 7. Paradigm Comparison

| Dimension | Engram | Lisp | Dataflow | Erlang | SQL |
|---|---|---|---|---|---|
| Code = data | ✓ (Memory nodes) | ✓ (s-expressions) | ✗ | ✗ | ✗ |
| Macro expansion | ✓ (templates → habits) | ✓ (defmacro) | ✗ | ✗ | ✗ |
| No call stack | ✓ | ✗ | ✓ | ✗ | ✓ |
| Reactive triggers | ✓ | ✗ | ✓ | ✓ (receive) | ✗ |
| Weighted control | ✓ (gradients) | ✗ | ✗ | ✗ | ✗ |
| Persistent substrate | ✓ (SQLite graph) | ✗ | env | process lifetime | ✓ |
| Self-modifying | ✓ (DISTILLATION) | ✓ | ✗ | ✗ (hot-reload) | ✗ |
| Biological grounding | ✓ (primary design axis) | ✗ | ✗ | ✗ | ✗ |

**Closest ancestors:**
- **Lisp macros** — code = data; macros expand at compile time (seed time in Engram). The s-expression is to Lisp as the Memory node is to Engram.
- **Hebb's rule** — "neurons that fire together wire together." The wiring IS the program. Engram takes this literally: there is no program separate from the engram substrate.
- **Dataflow / reactive systems** — triggers, no call stack, async propagation. Engram adds weighted scoring and biological grounding.
- **Cerebellum motor programs** — parameterized templates that instantiate into synaptic connectivity during learning. At execution time: just neurons firing, no template. Same principle.

**What is NOT Engram:**
- Not a general-purpose language. Cannot express arbitrary computation without a primitive backing.
- Not Turing-complete in the classical sense. Expressiveness comes from the richness of the primitive set and the density of the graph, not from universality of reduction.
- Not imperative. There is no sequencing operator at the language level — only triggers, conditions, and the inhibitory landscape.

---

## 8. Implementation Status

| Component | Status | Location |
|---|---|---|
| Habit executor (BG scorer) | Live | `cognition/basal_ganglia.py` |
| Template engine | Live | `tools/template_tools.py` |
| 3-layer TEMPLATE node schema | Live (D209) | `tools/template_tools.py` |
| D201 condition spec | Live | `cognition/thalamus.py` |
| Primitive ops (D204) | Live | `tools/os_primitives.py` |
| WONDER template | Seeded | `claudecode/seed_templates.py` |
| BLOOM_INHIBIT as exec model | Live | BG scorer lateral inhibition |
| DISTILLATION | Not yet seeded | Ticket T-db-spreading-activation |
| CACHED_PROBE | Not yet seeded | Ticket T-cached-probe |
| T-reader-as-habit-program | Pending | Ticket T-reader-as-habit-program |

---

## 9. Architecture Layers

The engram system is organized in four layers:

| Layer | Name | Contents |
|---|---|---|
| 0 | Substrate | Memory nodes, Postgres, weighted edges, the graph |
| 1 | Instruction set | Engram primitives: EMITIF, BRANCHIF, FORKIF, LABEL, STOPIF, ENDIF, channels |
| 2 | System calls | 21 primitive patterns (SEARCH_AND_RESPOND, MEMORY_DEPOSIT, FILE_ITERATOR, etc.) |
| 3 | Standard library | Cognitive subroutines: planning, decomposition, observation, replanning |
| 4 | Applications | Workflow templates: sprint, coding loop, reading pipeline |

Layer 1 is implemented. Layer 2 patterns are seeded as TEMPLATE nodes. Layer 3 is the current design frontier.

---

## 10. Layer 3 — Cognitive Standard Library (D297, D298)

Planning is not a single engram — it is the composition of smaller cognitive bricks. These eight primitives are the foundational layer 3 components. Confidence threading runs through all of them; each brick emits a confidence signal to basket so downstream nodes can branch on certainty.

**Re-entrance principle**: these bricks are not one-shot. Planning recurs after every execution step — observe result → replan → act → observe. OBSERVE and REPLAN are the feedback loop that makes debugging work.

**Chaining model (D300)**: TWM is the interface channel between subsystems — not basket. Each brick writes its durable output to TWM; the next brick fires reactively when it observes its precondition in TWM. Basket is within-node scratch space only (ephemeral, local to a single execution). The cascade is emit+react, not a call chain. A brick does not "call" the next brick — it changes observable TWM state and the next habit fires when its threshold is met.

> Example: PARSE_GOAL writes `ACTIVE_GOAL` to TWM → SITUATE's trigger fires when it sees `ACTIVE_GOAL` in TWM → SITUATE loads context → writes `CONTEXT_LOADED` to TWM → DECOMPOSE fires. No function calls, no passed parameters between steps.

Basket keys in the table below are convenience outputs for same-turn in-node use. For multi-turn or cross-subsystem handoff, the durable form is the TWM write.

| Brick | Input (basket keys) | Output (basket keys) | TWM write | Purpose |
|---|---|---|---|---|
| PARSE_GOAL | user_input | parsed_goal, parse_confidence | `ACTIVE_GOAL` (singleton, TTL=300s) | Extract actual intent from surface input |
| SITUATE | parsed_goal | twm_loaded, situate_confidence | `CONTEXT_LOADED` + loaded memories | Load relevant cortex context into TWM |
| DECOMPOSE | parsed_goal | sub_goals[], dependency_map, decompose_confidence | `PLAN_READY` + sub_goals chunk | Break goal into ordered sub-steps |
| CONSTRAIN | sub_goals[], risk_signals{} | constraint_ok, violations[] | `CONSTRAINT_RESULT` (ok/violations) | Check plan against known constraints |
| OBSERVE | expected, actual | delta, observation_confidence | `DELTA` observation | Compare expected vs actual result |
| HYPOTHESIZE | delta, twm_loaded, time_direction | hypothesis, hypothesis_confidence | `HYPOTHESIS` chunk | Abductive reasoning: forward=anticipate risks, backward=explain observed delta (D298) |
| REPLAN | delta, sub_goals[] | sub_goals[], replan_confidence | `PLAN_READY` (updated) | Update decomposition given observation delta |
| SCOPE_CHECK | current_action, parsed_goal | scope_ok, drift_signal | `SCOPE_DRIFT` if drift detected | Verify action is still solving the original goal |

> **D298**: HYPOTHESIZE is the universal predictive-coding primitive. `time_direction=forward` is what was formerly ANTICIPATE (predict what could go wrong). `time_direction=backward` is abductive explanation (how might this delta have occurred). The brain does not distinguish predicting from explaining — same loop, two temporal orientations.

These bricks compose into planning programs via TWM state observation (D300):
- Basic plan: PARSE_GOAL emits `ACTIVE_GOAL` → SITUATE fires → emits `CONTEXT_LOADED` → DECOMPOSE fires → emits `PLAN_READY`
- Risk scan: `PLAN_READY` → HYPOTHESIZE(forward) fires → emits `HYPOTHESIS` → CONSTRAIN fires
- Execution loop: `PLAN_READY` → [act] → OBSERVE fires on result → emits `DELTA` → REPLAN fires → emits `PLAN_READY` (re-entrant)
- Debug loop: `DELTA` → HYPOTHESIZE(backward) fires → emits `HYPOTHESIS` → CONSTRAIN fires → REPLAN fires
- Scope guard: SCOPE_CHECK fires on any `current_action` TWM observation alongside execution; emits `SCOPE_DRIFT` if drift detected

No function calls between bricks. Each step fires because the previous step changed observable TWM state.

---

## 11. Execution Model: Emit+React and the Cognitive Milieu

*Added 2026-03-26. Supersedes the "cognition as pipeline" framing.*

### The Fundamental Primitive

**The cognitive milieu is the substrate. Emit+react is the primitive. Everything else is subtree shape.**

Something emits into the shared cognitive space → nodes sensitive to that emission react → reactions may themselves emit → eventually something rises to the attentional layer → output.

"Pipeline" was wrong because pipelines are linear. The milieu is n-dimensional: many things can emit and react simultaneously. The DAG is the correct shape.

All cognitive reactions — greetings, tool calls, habit chains, memory surfaces, NE arcs — use the same emit+react pattern on different subtrees. What varies is subtree depth and shape, not the primitive.

### Two Capacity Levels

**Sub-attentional** — the DAG nodes. Parallel, abundant, fast, cheap, mostly invisible. TWM lookups, inhibition checks, "who asked", temporal gradient reads. Run speculatively — a check that races and loses is nearly free. By the time the attentional layer needs a result, the sub-attentional work is already done.

**Attentional** — what lands in TWM at the top. The ~7-item limit applies here. The ring buffer models this bottleneck. What rises is the winner of the sub-attentional races, already resolved.

The ~7 limit is the integrator's bottleneck, not the system's capacity. Akien: *"I can see them if I look hard, but even for me, I'm really only aware at this level with great focus."*

### The Inhibition Layer

Between habit selection and action execution lies a DAG of conditional gates — the inhibition layer. The action only fires if nothing inhibits it. Current code has zero inhibition nodes; tools fire unconditionally after habit selection. This is the next architectural gap.

Example inhibition chain for `get_current_time`:
```
TWM check: do I already know? (episodic, temporal-aware)  →  yes → short-circuit
Inference check: can I derive it?                         →  yes → short-circuit
Estimate check: can I reason from elapsed time?           →  yes → short-circuit
Action gate: is this action blocked?                      →  no  → proceed
  → tool fires
```

Temporal gradient checks ("when did I last look?", "how long ago?") live here, not in inference.

### Process Time Is the Pause

Parallel execution means natural process latency IS the thinking time. Don't stack: `tool_call(500ms) + inference(800ms) + artificial_pause(500ms) = 1800ms` when `parallel = max(500, 800) = 800ms`. Fork at the earliest branch point, join at the latest necessary point. Start expensive operations as soon as you know you'll need them.

---

## 12. The Basket

*Added 2026-03-26. Defines execution context for Engram threads.*

### Structure

Each execution thread carries a **basket**: a shared dict passed as a pointer, not a deep copy. When a fork happens, both threads hold a reference to the same basket instance. This correctly mirrors biological hardware constraints — brains don't deep-copy working context on a fork.

### Fork and Merge

- **Fork**: both threads share the basket pointer; as they execute, each writes its own keys
- **Merge** (explicit join, distinct from "meeting in the milieu"): baskets merge key by key at the join point
- **Write collision**: allowed and logged, not fatal. Two branches writing the same key is a design signal — the keyword contracts need attention. Log the collision; look for logic failures downstream. Repeated collisions on the same key mean the subtree was designed wrong.

### Keyword Contracts

Each node declares: which basket keys it reads, which it writes. No two concurrent branches should write the same key — this is the design-time invariant. Enforcement is by contract discipline at the design layer, not by runtime locking.

### Basket as Provenance

When a thread completes (done or part-done), the basket state at completion attaches to the resulting memory as provenance.

```
episodic_result.basket = {
  who_asked: "leah",
  source: "get_current_time",
  inhibited_by: null,
  format_decision: "24h",
  resolved_at: 1711461803.4
}
```

"Why did Igor say 14:23?" → read the basket on that episodic record.

**Part-done is a valid result state.** An inhibited thread deposits a memory with the basket snapshot at point of inhibition: "I was going to do X, got stopped by Y, here's what I knew when I stopped." That's a training signal: this basket state → this inhibition = pattern to learn.

---

## 13. Engram Segment as Composable Unit

*Added 2026-03-26.*

An **Engram segment** is a reusable, expandable piece of Engram code. The "class?" question:

| OOP concept | Engram equivalent |
|---|---|
| Class definition | Segment — defines DAG shape, basket keys, fork/join topology |
| Runtime instantiation | Activation — thread spins up carrying a basket |
| Object instance | Executing thread + basket |
| Instance state (fields) | Basket contents |
| Subclassing/inheritance | Parameterized expansion at seed time |
| Method call | Emission into the milieu that activates a node |
| Call stack | Absent — replaced by basket |

**Key difference from OOP classes**: classes instantiate on demand at runtime. Engram segments expand once at seed time — the nodes are already deployed in the graph, waiting for the right emission to activate them. "Instantiation" happened at deposit time.

**Segment = class. Expansion = compilation. Activation = execution. Basket = instance state.**

A segment is class-like but with the call stack replaced by the basket. Composing segments means embedding one DAG structure into a larger one, with compatible basket contracts.

---

## 14. Design Principles

1. **The engram IS the program.** No code outside the graph is authoritative at runtime. Python is bootstrap scaffolding that comes down as the graph densifies.

2. **Templates are seed-time macros, not runtime subroutines.** Expand once, run as habits. No call overhead, no namespace, no return address.

3. **Gradients over branches.** BG scoring gives every candidate a continuous weight. The winner is not chosen by an `if` — it emerges from competition.

4. **DISTILLATION is load-bearing.** A matrix that cannot compress will accrete without limit. Every growth operation needs a paired compression pathway.

5. **BLOOM_INHIBIT is not optional.** It is the execution model. Patterns that appear to need a scheduler are actually underspecified — the inhibitory landscape provides scheduling for free.

6. **Primitives, not frameworks.** The primitive set should be minimal and composable. Complexity lives in the pattern layer, not in op implementations.
