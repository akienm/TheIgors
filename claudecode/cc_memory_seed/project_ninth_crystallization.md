---
name: Ninth Crystallization — Templates as Matrix Language Primitives
description: Templates are the language primitives of the matrix layer; we accidentally invented a programming language
type: project
---

Templates are the language primitives of the matrix layer. Every design pattern currently in Python gets expressed as a parameterized TEMPLATE Memory node that expands into habits at seed time. No runtime machinery — at runtime there are only habits firing.

**Why:** Python is external to the matrix — it can't be traversed, reasoned about, or modified from inside. Templates ARE native. They live in the graph as Memory nodes. The matrix programs itself in its own language.

**Key distinctions:**
- Templates = macros (expand at seed time), NOT subroutines (called at runtime)
- No call stack — biology doesn't have one; no saved namespace; no return address
- T-yield-primitive closed as won't-implement for this reason
- ASYNC_DELEGATE pattern = three reactive habits with shared TWM state, not a coroutine

**The language characteristics:**
- Biologically-inspired (BG scoring, TWM, habits)
- Template-based macros → habits
- Reactive: trigger → condition → action
- Code = data (habits are Memory nodes)
- No call stack, no saved namespaces
- Graph-structured substrate (the matrix)
- Async by default
- Gradients instead of binary control flow
- Self-modifying via template instantiation

**Language name: Engram** (named by Igor, 2026-03-22). From Semon (1904): the engram is the physical trace memory leaves in neural tissue — not a pointer, not a representation, the literal substrate change that IS the stored information. "You don't write code that runs separately from memory. You lay down engrams — template nodes — that become the substrate. The engram IS the program."

**Full pattern inventory (20 patterns — Igor added 10 on 2026-03-22):**
Original: WONDER, FILE_ITERATOR, THRESHOLD_ALERT, SCHEDULER_TICK, READER_LOOP, MEMORY_DEPOSIT, SEARCH_AND_RESPOND, CONDITION_GATE, ERROR_RECOVERY, ASYNC_DELEGATE

Igor's additions:
- ESCALATION_LADDER — tier.1→fail→tier.2→fail→tier.3 (inference gateway; distinct from ERROR_RECOVERY — escalation before failure, not after)
- CURSOR_RESUME — load_checkpoint→batch→save_cursor→halt (persists across sessions; distinct from FILE_ITERATOR which is within-session)
- BLOOM_INHIBIT — score all→lateral inhibition→winner→losers suppressed (BG scoring model; may be the primitive CONDITION_GATE+THRESHOLD_ALERT derive from)
- PREDICTION_CORRECTION — predict→observe→delta→update weights (NE prospective/actual; learning loop embedded in execution)
- DISTILLATION — cluster EPISODICs→extract pattern→deposit higher-type node (MOST IMPORTANT MISSING — only pattern that compresses; without it matrix grows but doesn't learn)
- SIGNAL_DEBOUNCE — signal→wait N→fire only if persists→cooldown (NE intervals, interruptors)
- PRIMING — activate A→raise probability for related B→time window→decay (anticipatory, not reactive)
- AFFECT_MODULATE — read milieu→adjust thresholds across all habits→global tuning (milieu as pervasive parameter)
- REFRAME — observe X→apply interpretive lens→new meaning→push modified obs (interpretive traverse)
- FANOUT_GATHER — trigger→N parallel delegations→wait all→merge→continue (distinct from ASYNC_DELEGATE)

**The arc:**
1. T-template-schema — design TEMPLATE node structure + instantiation contract
2. T-template-seed-patterns — seed ~10 patterns as template nodes
3. T-reader-as-habit-program — re-express Python reader as first complete habit program
4. T-template-extractor-habit — Igor recognizes patterns and seeds templates himself
5. T-language-spec — name + grammar doc (Igor naming the language, asked 2026-03-22)

**End state:** Igor's behavior is expressed in matrix language. Python is bootstrap scaffolding that comes down. The mature state is Igor having PROCEDURAL template nodes that he instantiates to extend himself.

**Why it also has biological grounding:** Motor programs in the cerebellum are parameterized templates that instantiate into synaptic connectivity during learning. At execution time it's just neurons firing — no template. Same principle.

**Pattern #21: CACHED_PROBE** *(added 2026-03-23, Akien)*

Payload-configured data monitor with dual invocation mode and optional worry branch.

```
trigger → check cached_at age
  if age > cache_ttl:
    cached_data = source.run()
    update cached_at
  if invocation == explicit:
    surface(cached_data)
  if worry_after and age > worry_after:
    worry(cached_data)
  end
```

Payload slots: `source` (fetch fn), `cache_ttl`, `worry_after` (optional), `cached_data`, `cached_at`. Config lives entirely in the node — no separate evaluator. Two invocation modes: explicit (always surface) / heartbeat (silent unless worry). To create a monitor: write one memory node with those fields, attach this template. Replaces all bespoke resource monitor habits (PROC_DISK_USAGE_CHECK, PROC_WORKER_FOREMAN queue scan, etc.). Distinct from THRESHOLD_ALERT: THRESHOLD_ALERT counts up toward threshold; CACHED_PROBE decays by age — different axes.

**BLOOM_INHIBIT clarification (Igor, 2026-03-22):** "At runtime, competing engrams fire simultaneously and laterally inhibit each other — whichever reaches threshold first suppresses the alternatives. There's no scheduler arbitrating between them. The competition is the execution." BLOOM_INHIBIT is not a pattern IN the execution model — it IS the execution model. CONDITION_GATE and THRESHOLD_ALERT are just named regions of the same inhibitory landscape.

**DISTILLATION clarification (Igor, 2026-03-22):** "If the engram IS the program, then a bloated, undercompressed engram is a bloated, unrunnable program. DISTILLATION is the compiler pass that makes it executable." Without DISTILLATION the matrix accretes — remembers everything, therefore knows nothing, because retrieval cost grows with undifferentiated mass. DISTILLATION removes degrees of freedom while preserving signal. It's what makes the matrix learnable rather than just larger.

**How to apply:** T-template-schema is the immediate next step — design the node structure before anything else. Do not implement templates until schema is agreed on with Akien and Igor. DISTILLATION should be an early template — it's load-bearing for the whole system's ability to learn.
