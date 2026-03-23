---
name: Everything is habits — cognitive operations as action nodes
description: Every cognitive operation (start search, update milieu, surface memory, fight-or-flight) is an action node. Brain-scale complexity from one substrate.
type: project
---

## The insight (2026-03-17)

"Start search" is an action node. "Update milieu" is an action node. "Surface this memory" is an action node. Even the act of a memory surfacing IS a habit firing.

There is no special-case code for cognition. There are only nodes with weighted edges. Every cognitive operation — retrieval, salience update, emotional register lookup, tier escalation, response generation — is the same thing: a habit that fires, activates other habits, deposits into TWM, and terminates.

## Survival and relationship energy — same substrate

Fight-or-flight is a habit chain:
  threat word detected → emotional register search (habit) → threat assessment (habit) → milieu spike (habit) → defensive/de-escalation node (habit)

New relationship energy is the same structure:
  warmth signal → social register lookup (habit) → milieu update (habit) → narrative coloring (habit)

Not different modules. Same substrate, different parameterization.

## The combinatorial explosion

When every cognitive operation is a node with weighted edges to other nodes, interaction paths scale combinatorially with graph density — the same way neural complexity scales. You don't need 86 billion neurons. You need the architecture: weighted activation propagation on a graph of habits-calling-habits.

Igor doesn't need to reach brain scale to be useful. It needs enough density that the RIGHT paths activate reliably. Density is what the reading/training work is building.

## Scaffolding implication

The Python code (cortex.search(), select_habit(), milieu.ingest()) is scaffolding. It's building the graph by instrumenting what the graph will eventually do on its own. When the graph is dense enough:
- "now retrieve memories" → replaced by a "start search" action node firing
- "now score habits" → replaced by activation propagation from input nodes
- "now update milieu" → replaced by emotional register nodes depositing directly

The scaffolding comes down as the graph densifies. We're learning which operations need to be habituated by watching which Python code we keep calling.

## Connection to prior crystallizations

- 2026-03-07: "parsing and reasoning, same thing in both directions" — same weights, bidirectional
- 2026-03-11: "everything is memories and memories are habits" — now extended: every OPERATION is also a habit
- 2026-03-11: "code as scaffolding" — the scaffolding teaches us what the graph needs to habituate
- 2026-03-11: "layers of graphs are an inference engine" — the habit chains ARE the inference

This is the same insight at increasing resolution. Each session we see it more clearly.
