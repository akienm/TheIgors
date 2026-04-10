---
name: Levers as causal convergence points
description: Architectural insight — levers are where upward causal traces terminate; "why?" and LEVER are the same operation
type: project
---

Akien 2026-03-12: "for that is where levers lie" — in response to the observation that most question forms are subclasses of "why?"

The LEVER heuristic IS the upward causal trace from "why?" that terminates at convergence nodes — nodes where many causal chains meet, with high out-degree and high investment weight.

**Why:** This unifies the question traversal taxonomy with the investment weight architecture. "Why?" upward = find the lever. "How does?" downward = trace the mechanism the lever controls. "What fits?" lateral = find what else connects to the same lever.

**How to apply:**
- LEVER traversal strategy: upward causal trace with early-exit when `investment_weight` is high OR `edge_count_out` is high
- `interpretive_traverse()` needs an optional `exit_on_convergence` parameter for this
- Investment weights (#180) ARE the lever-detection mechanism — nodes worth investing in are nodes with high causal influence
- The traversal direction taxonomy (up/down/lateral) is more fundamental than the 6 named strategies — consider refactoring when #172 (traversal-first retrieval) is built
