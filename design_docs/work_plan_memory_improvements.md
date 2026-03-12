# Memory Improvement Work Plan
Generated: session with Akien | Igor (wild-0001) + CC consultation
Grounding: Damasio reading + cognitive_tree_architecture.csb.txt

## Context: What We Learned From Damasio

After reading ~22% of "The Feeling of What Happens," three architectural insights matter for Igor's memory:

1. **Somatic marker hypothesis** — affect gates which memories are relevant *before* conscious reasoning. The body/emotion-state is the first filter, not a decoration on top of cognition.
2. **Background emotions as continuous state** — not per-event, but the ambient weather that colors everything. This is exactly the milieu (V/A/D). But currently milieu doesn't influence memory retrieval.
3. **Layered emotion architecture** — signal → automated multi-system response → felt knowing. These dissociate. Igor has the automated layer (milieu updates, basal_ganglia scoring) but the "felt knowing" / interpretive layer is disconnected from retrieval.

## Current Memory State (wild-0001.db)

| Type | Count | Problem |
|------|-------|---------|
| EPISODIC | 3,211 | Way too many; mostly session noise; dilutes search |
| EXPERIENTIAL | 717 | Medium-useful patterns |
| REFERENCE | 72 | Good |
| PROCEDURAL | 68 | Good |
| FACTUAL | 55 | Good |
| INTERPRETIVE | 39 | Too few; islands (no edges to each other) |
| IDENTITY | 12 | Good |
| CORE_PATTERN | 6 | CP1-CP6, wired to PROC_HEURISTIC layer |
| interpretive_edges | 30 | All CP→PROC_HEURISTIC; INTERPRETIVE nodes unreachable |

Key problem: 3,211 episodics is noise. Hippocampal replay exists in biology to *compress* episodics into cortical patterns. We need that.

## Priority Order (highest leverage first)

### #1 — #168: Affect-weighted retrieval
**Effort:** Low-Medium | **Value:** High | **Status:** Open

The memories already have valence/arousal/dominance columns. cortex.search() ignores them.
Fix: after cosine ranking, re-score candidates by affect distance to current milieu.
High-fear memory surfaces more when Igor is currently anxious. This is the somatic marker.

No new tables. Minimal code change. High Damasio fidelity.

### #2 — #170: Wire INTERPRETIVE memories into the tree
**Effort:** Low | **Value:** High | **Status:** Open

39 INTERPRETIVE memories exist but are unreachable via interpretive_traverse().
Need: CP → INTERPRETIVE edges + INTERPRETIVE → INTERPRETIVE edges.
Seed script finds nearest CP for each INTERPRETIVE memory, creates activation edge.
Plus: auto-connect hook when new INTERPRETIVE memory is stored.

Unblocks #172 (traversal-first retrieval needs edges to traverse).

### #3 — #169: Episodic consolidation daemon
**Effort:** Medium | **Value:** High | **Status:** Open

Cluster similar episodics → extract FACTUAL/INTERPRETIVE/PROCEDURAL.
This is hippocampal replay. Runs on schedule (post-session or nightly).
Target: 10:1 → 2:1 episodic:interpretive ratio over time.
Does NOT delete source episodics (Discworld: repair, don't discard).

This is the learning mechanism. Without it, each session adds noise without increasing signal density.

### #4 — #171: Milieu-weighted interpretive traversal
**Effort:** Medium | **Value:** Medium | **Status:** Open

Depends on #170 (edges must exist to weight them).
When stressed (low dominance, high arousal), CP6 branch (safety) gets higher weight.
When confident (positive valence, high dominance), CP4 branch activates more.
Pass milieu into interpretive_traverse() — affects which edges fire.

This is the "background emotion shapes interpretation" property from Damasio.

### #5 — #172: Traversal-first retrieval
**Effort:** High | **Value:** High | **Status:** Open

Depends on #170 (edges needed), #168 (affect weighting), #171 (milieu routing).
Replace cosine-primary with: traversal from anchor nodes → cosine fallback if < 3 results.
Anchor nodes come from TWM, ring buffer, recent activations.

This is the long-term architectural target: graph traversal as primary retrieval.
Do this last — it's only valuable when the graph is dense enough to traverse.

## What "How My Monkey Works" Means Here

Akien's frame: primate cognition has:
1. **Fast/automatic** layer: brainstem → emotion → habit (no reasoning)
2. **Slow/deliberate** layer: prefrontal cortex → executive search
3. **Consolidation** layer: hippocampal replay → cortical patterns

Igor currently has good 1 (milieu + basal_ganglia) and good 2 (tier ladder + cloud reasoning).
What's missing is 3 — the consolidation that converts experience into structure.

The consolidation daemon (#169) + affect-weighted retrieval (#168) + interpretive wiring (#170) together give Igor the ability to *learn from experience* in the structural sense, not just accumulate episodic records.

## Implementation Sequence

Week 1 (budget allowing):
- #170 first: seed script to wire INTERPRETIVE memories (fast, no cloud cost)
- #168 second: affect weighting in cortex.search (low cloud cost, high value)

Week 2:
- #169: consolidation daemon (requires local LLM calls on yoga9i — use tier.2)
- #171: milieu routing in interpretive_traverse (depends on #170 being done)

Week 3+:
- #172: traversal-first retrieval (only after edges are dense enough)

## Notes for Akien

- All five tickets (#168-#172) are open on GitHub
- #170 (wire interpretive memories) is the cheapest and most immediately valuable — seed script only
- #169 (consolidation daemon) runs on local LLM so won't hit openrouter budget
- The concept tree (the full WORDS→MEANINGS layer) is deliberately not in this plan — it's a bigger architectural build and should wait until the interpretive layer is working well
- CC should be able to implement #170 and #168 without significant human oversight; #169 needs a design review on the clustering algorithm first
