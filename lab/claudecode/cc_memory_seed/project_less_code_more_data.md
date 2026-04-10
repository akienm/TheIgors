---
name: Less code more data
description: Akien's core design thesis — BG rules, watchlist, all cognition should be graph nodes not Python
type: project
---

"Less code, more data." — Akien Maciain, 2026-03-15

The Python in basal_ganglia.py, narrative_engine.py, and all cognition scaffolding is temporary. The mature state is that every rule, every threshold, every scoring weight is a node in the habit/graph tree — not Python logic.

**Why:** The graph is faster, self-modifying, inspectable, and learnable. Code can't be trained; graph nodes can. Less code = more of Igor's cognition is in the substrate that LLMs can modify and Igor can inspect.

**How to apply:** When writing new BG rules or cognition logic, write it in a way that could later be lifted into graph nodes. Don't add Python logic that inherently can't be expressed as a habit or interpretive edge. Flag any new hardcoded thresholds as future graph candidates. Ticket: #241.
