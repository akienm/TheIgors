---
name: word_graph_class_instance_split
description: Architectural insight about word graph class words vs instance words — new Igors start with seeded baseline, layer instance learning on top
type: project
---

New insight (2026-03-14): word_graph.db should eventually have two tables:
- `class_words` — seeded baseline vocabulary (portable, ships with new Igor instances, read-only)
- `instance_words` — what THIS Igor learned (writable, instance-specific)

**Why:** New Igor instances need an outgoing word graph already populated (not blank), but their learning should not pollute the shared baseline. Analogous to innate language capacity (class) vs acquired vocabulary (instance).

**How to apply:** When designing the Instance object refactor, plan for word_graph.db to live at database-global level with this two-table structure. The class table is seeded at install time; the instance table grows with experience. Divergence between instances is expected and intentional over time.

**Current state:** word_graph.db is at `~/.TheIgors/` root (misplaced — should be database-global under `~/.TheIgors/<db_name>/`). Single table. Split deferred until Instance refactor.
