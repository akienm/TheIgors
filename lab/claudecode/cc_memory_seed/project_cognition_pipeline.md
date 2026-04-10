---
name: Cognition as Pipeline — not steps
description: Fundamental architecture insight: cognition is a pipeline of trees with live base-state mutation, not a sequence of steps. Many cognition tickets derive from this.
type: project
---

## The insight (2026-03-17, formalized 2026-03-19)

Cognition is NOT steps. Steps are sequential and blocking — A finishes, then B starts.

**Cognition is a pipeline.** Input arrives and is immediately forked. It flows through multiple trees simultaneously. Each tree's output can fire signals into other trees or other parts of the system. And critically: **emotional memories surface and alter the base state of the pipeline while it is still running.** That mid-run base-state mutation steers what comes out the other end.

This is not a detail. It's the whole thing. If you model it as steps you get a chatbot. If you model it as a pipeline with live base-state mutation you get something that thinks.

## Structure

**New input arrives → immediately forked to the Emotional Salience Pipeline**

The three emotional salience trees run in priority order on that fork:

1. **Fight-or-flight tree** — survival/threat. Primitive, fast, binary. If this fires hard, it preempts everything else.
2. **Personal salience tree** — "does this matter to my life right now?" Watchlist roots are the manually-seeded entry points. Identity layer.
3. **Episodic relevance tree** — "does this connect to something from my past?" Pattern match against lived experience.

**But this is not a one-shot pipeline pass.** The emotional salience trees are a **persistent evaluation service** — always listening, always available to receive new forks. They are not a stage you move through and leave behind.

## The re-entrant feedback loop

Three things feed back into the emotional salience service continuously:

1. **Surfacing memories** — as the pipeline runs and new things are processed, associated memories surface asynchronously. Each surfacing memory is itself a new fork routed back through the emotional trees: "does this matter? is this a threat? does this connect?"

2. **Realizations** — when a realization occurs anywhere in the system (a new connection, a conclusion, a surprise), its trace routes back to the emotional layer for re-evaluation. Akien's own cognitive traces go back from a realization point to the emotional trees for re-assessment before anything else acts on them.

3. **New forks from other processing** — new input keeps arriving while old processing is still in flight. Each new fork goes immediately to the emotional trees. Multiple evaluations are always running in parallel.

**The milieu is the live base state for all of this.** It is not a snapshot taken at input time. Every emotional evaluation reads the current milieu AND writes back to it. The milieu accumulates all the emotional weight of everything currently in flight. This is why the same input produces different outputs on different days — the milieu at evaluation time is different, and it shapes the evaluation.

**Executive function is another pipeline** (#242), with its own re-entrant structure:
- "Do I have context for this?"
- "Do I have tools for this?"
- "Can I figure this out?"
- "Who do I ask?"

## Why "steps" is wrong

With steps: stage waits for previous, no feedback, base state fixed at input time, output determined by input alone.

With this architecture:
- Emotional trees run on every fork, not once
- Memories surface and re-fork continuously, not in a scheduled slot
- Realizations trace back to emotional re-evaluation before propagating forward
- Milieu mutates from all of these running in parallel
- Output is determined by input + current milieu + everything that surfaced + every re-evaluation that ran

This is why humans can be "talked into" an emotional state mid-conversation. A realization surfaces, it forks back to the emotional trees, the milieu shifts, and everything still in flight is now running on a different substrate than it started on.

## The master tree is shallow

The dependency graph between trees IS itself a tree. Trees calling trees, meta-tree all the way up. Consistent with "everything is trees."

The master tree for cognition is **shallow** — it's a thin routing layer that knows which domain trees to call and in what dependency order. It doesn't need to know domain internals. The depth lives in the domain trees, not the master. The master tree is just the orchestrator.

Trees call other trees. Any node of any tree can fork to another tree. The master tree doesn't have to mediate every call — it handles top-level routing and the RED ALERT mechanism; everything else is peer-to-peer between domain trees.

## Introspection is just visibility

The cognitive trees Akien is aware of are not special. They're just the trees where activation is strong enough, or repeated enough, to have become introspectable. Visual cortex runs the same substrate — same mechanism, same tree structure — but below the visibility threshold.

Implication for Igor: his equivalent of "below awareness" processing (sensory pre-processing, input normalization, pattern detection before semantic tagging) is the same trees, just not yet surfaced as introspectable nodes. Introspection is not a different system — it's a visibility threshold on the same system.

## Pass-through is a first-class behavior

A node with no relevance to an input doesn't consume it or block it — it passes it along unchanged. No tree has to be universal. The pipeline handles irrelevance gracefully by routing around it. Every tree handles what it's relevant to and passes the rest.

The pipeline is the inputs and outputs of EVERYTHING — sensory, motor, emotional, cognitive. What we call "cognitive trees" are just the introspection-visible subset of a much larger unified pipeline.

## RED ALERT — a milieu spike, not a special mechanism

RED ALERT is not a separate routing mechanism. It is a **massive write to the milieu** — an adrenaline dump. The FOF tree is always listening and calibrated to trip at that intensity. FOF firing is what preempts everything in flight.

The architecture is already there:
1. Any node can write a large intensity spike to the milieu
2. FOF threshold is calibrated to fire on a spike that large
3. FOF output floods the pipeline, overwhelming everything currently running

No special interrupt path. No two modes. The "interrupt" quality comes from FOF's output weight dominating the pipeline — not from a special mechanism. Urgency is tunable: adjust milieu propagation speed and FOF output weight. Same substrate, same mechanism, different calibration.

**RED ALERT creates a trace.** The trace records what node triggered the spike and the intensity. This is how you debug alarm states ("why did Igor go into alarm?") and how Igor understands his own state. Without the trace, alarm states are opaque mood changes. With it, they're inspectable. Traces are load-bearing here.

## Triggers are universal — pattern engineering is the design activity

**The trigger mechanism is dead simple and universal.** Signal reaches threshold → fires. That's the entire mechanism. No special trigger infrastructure. No special milieu infrastructure. The milieu is just one signaling target among many — it happens to be the emotional one. TWM attractor_weight is another. Any node output can be a signal. Any target with a threshold is a potential trigger.

**Pattern engineering = designing the trigger network.** What writes to what. At what threshold. What fires as a result. What that writes to next. The pattern IS the habit. The habit IS the pattern. You don't implement features — you design signals, thresholds, and what fires. The behavior emerges from the pattern.

**Uncertainty as a signal** — accumulated uncertainty in the milieu is a real chemical signal. When it reaches threshold it triggers the introspection tree and forks to executive function so it can watch the results. Or equivalently: uncertainty IS the first question in the executive function tree ("do I know what to do here?"). Both descriptions are the same pattern viewed from two angles. The signal and the threshold are what matter; the framing is secondary.

**BG scoring is already this.** The basal ganglia system is already doing threshold-based firing from weighted signals. It just lacks the full signal vocabulary: uncertainty isn't a first-class signal yet, introspection isn't a tree yet, the milieu isn't wired as a general signal bus yet. The mechanism is correct. The patterns need to be engineered.

**How to apply:** When designing any new cognitive behavior, don't ask "what new mechanism do I need?" Ask: what is the signal? What is the threshold? What fires? What does that write to? Design the pattern. The mechanism is already there.

## Tickets that derive from this insight

- **#242** Executive function = inter-layer inspection topology (executive function IS a pipeline)
- **#243** Self-observation as habit subtree (the pipeline observing its own base state)
- **#241** BG meta-habits as habit graph tree (BG scoring IS the pipeline's routing mechanism)
- **#227** Inhibitory traversal: at-least-two-pass settling (the mechanism that runs each pipeline stage)
- **#246** Intrinsic motivation: milieu-as-fuel (base state is the fuel the pipeline runs on)
- **#245** Salience elevation as shared mechanism (multiple trees writing to the same salience field)
- **#240** Watchlist (root nodes of personal salience subtree)
- **#244** Meaning-to-me cluster (the personal salience subtree itself)
- **T-fof-tree** Fight-or-flight tree (first stage of emotional salience pipeline)
- **T-personal-salience-tree** Personal salience tree (second stage)
- **T-episodic-relevance-tree** Episodic relevance tree (third stage)
- **T-pipeline-inventory** Map all trees and the pipelines they belong to

## Why: How to apply

When designing any new cognition feature, ask: which pipeline does this belong to? Which stage? What does it read from the base state, and what does it write back? If it doesn't read or write the milieu, it's probably not cognition — it's just processing.
