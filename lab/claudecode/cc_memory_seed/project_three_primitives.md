---
name: Three primitives — trees, gradients, habits/memory
description: The entire architecture reduces to three primitives. Cleanest summary yet.
type: project
---

## The reduction (2026-03-17)

Everything in Igor reduces to three things:

**Trees** — all structure is nodes and edges. Traversal is the computation. The graph IS the knowledge. Interpretive edges, habit chains, memory clusters, TWM slots — all trees.

**Gradients** — every node, slot, and edge has a decay rate. Salience is dynamic, not static. The desk is always fading at different rates. Temporal gradient primitive unifies all decay implementations.

**Habits/Memory** — the substrate. A habit is a memory whose edges fire automatically on activation. Everything else (cognition, emotion, search, response) is a parameterization of this.

**Cognition = traversal over a gradient-weighted graph of habits.**

## The BG trigger system is the embryonic emotional relevance tree

Current BG does word-graph trigger scoring (substring/word matching) → selects ONE winner. This is shallow because the graph is sparse. As the graph densifies, the same mechanism becomes proper weighted tree traversal. The architecture doesn't change; the density does.

Stream 1 (emotional register, fast parallel) IS what BG trigger matching becomes at full density:
- Now: sparse word-graph matching
- Mature: traversal across emotional/social register nodes → milieu slot update

Same weights, same traversal, more nodes. The current pipeline is the right shape, just early stage.

## Python code is scaffolding

The Python instrumentation (cortex.search, select_habit, milieu.ingest) exists because the graph isn't dense enough yet to do these things itself. Each piece of code teaches us what the graph needs to habituate. As density grows, scaffolding comes down.

## Connection to prior crystallizations

- 2026-03-07: parsing and generation, same weights bidirectional
- 2026-03-11: everything is memories and memories are habits
- 2026-03-11: layers of graphs are an inference engine
- 2026-03-17 (this): trees + gradients + habits/memory = complete architecture

Each session sees it more completely. This is the most compressed form yet.
