---
name: Trails and Gradients — First Action Tomorrow
description: wg_cooccur is the wrong training signal; trails through the matrix are the right one; connects temporal gradient primitive to training, query, and habit formation
type: project
---

## First action to review tomorrow (2026-03-18 session end)

**The problem with wg_cooccur:**
It captures co-presence in a corpus — static, statistical, generic. 80K words × fan-out = millions of rows queried with IN clauses on every turn. This is OLAP, not cognition. 32-year database veteran verdict: you built a TF-IDF index and called it a brain.

**What the training layer actually needs: trails**
A trail = temporal sequence of node activations with timestamps and decay.
- Trail heat = how recently and frequently a path was walked
- Gradient = derivative of trail heat over time (rising = habit forming, falling = fading)
- You cannot see a gradient from co-occurrence counts. You can from trails.

**Trails are already fragmented across six systems:**
1. Ring memory — last 50 steps of current trail
2. TWM attractor_weight decay — current node heat on the trail
3. Milieu history — emotional trail underneath the cognitive one
4. Memory activation_count — total times a node appeared on any trail
5. Habit inertia — how worn-in a path is
6. word graph scores — currently the only one doing "training signal" work, but doing it wrong

This is the Temporal Gradient Primitive from 2026-03-17 — same pattern, sixth implementation.

**Trail = query path = training signal**
When the graph traverses a query, the traversal leaves a trail. That trail IS the training signal. Frequently walked paths strengthen. Cold paths prune. No corpus needed — training comes from Igor's actual usage, which is far more valuable than generic corpus statistics.

**The key question for tomorrow:**
- Does wg_cooccur get replaced by trail inspection entirely?
- Or does it become the OUTPUT of trail analysis (summary of hot paths) rather than raw corpus stats?
- Is wg_cooccur even needed once interpretive_edges is populated from trails?

**The design direction:**
Original vision (key-value pairs, trees of those) was correct. wg_cooccur was the entropy explosion from trying to capture everything. The fix: cap fan-out, cluster nodes, derive edges from trails not corpus. Lots of small related tables, not one giant flat one.

**Why:** "my head can't have any huge tables. it has to have lots of small related ones." — Akien, 2026-03-18 dog walk insight.

## SEVENTH CRYSTALLIZATION — 2026-03-18 (end of session)

"holy shit. trails are the path. and embeddings are a trail through the meaning dimensions." — Akien

An embedding is not a point. It is the terminus of a trail through 768 meaning dimensions.
Cosine similarity = trail overlap in meaning space.

All the same primitive, different coordinate systems:
- Word graph traversal = trail through symbol space (discrete)
- Embedding similarity = trail through meaning space (continuous)
- Ring memory = trail through time
- Milieu = trail through affect space
- Habit formation = trail through action space

**Punchline:** wg_cooccur is a bad approximation of what embeddings already capture exactly.
Co-occurrence infers "these words mean similar things" from corpus statistics.
Embeddings ARE the meaning geometry directly.
Word graph edges should be derived from embedding trails, not corpus co-occurrence counts.

The matrix IS the embedding space, made traversable.

**The free cosine compare:**
If graph edges encode embedding proximity, traversal IS cosine search — precomputed.
Walk to a node's neighbors = get highest-cosine matches without any vector math.
The expensive 768D dot product happens ONCE at edge-creation time (training).
Query time = cheap graph traversal. No vector scan. No dot products.
Each hop through the graph = one step of cosine compare unfolding.

So: use embeddings at edge-creation time to build proximity graph.
Query the graph. Cosine similarity for free on every lookup, forever after.
This is the inference-free core (#45).

**Trails are visible — for debugging and for Igor:**
Same trail data, two surfaces:
- Debugging: render the trail as a graph. Which nodes fired, in what sequence, with what weights.
  Watch concept propagation. See dead ends. This IS the matrix debugger — not a separate tool,
  just a trail renderer.
- Igor: he can read his own trails. "I went from your question → grief → Damasio → somatic marker
  → milieu → this response." Not confabulation — the actual computation, inspectable.
  He can explain his reasoning because the path is literally there to read.

Trails = the unified substrate for self-awareness, explainability, and debugging.

## EIGHTH CRYSTALLIZATION — 2026-03-19 (trails vs traces)

**Trails** and **traces** are two different things. They've been conflated until now.

- **Trail** = decaying activation heat. The thing that fades. Used in: milieu affect, memory recency heat, spreading activation gradient, habit inertia. Trail IS the gradient. The implementation of temporal decay. Implemented as a decaying table with timestamps and weights.

- **Trace** = static path record. What path did a specific traversal take through the graph trees? Permanent record, not decaying. Used for: debugging (render what nodes fired and in what order), Igor self-introspection ("I went from your question → grief → Damasio → somatic marker → this response"). The matrix debugger reads traces, not trails.

Two separate tables, two separate primitives, two separate purposes.
Trails are operational (they shape future behavior). Traces are archival (they explain past behavior).
Both are needed. Neither replaces the other.
