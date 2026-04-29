# pursuits — Goal-bound behavioral units above engrams

**Path:** `theigors/subsystem_index/pursuits`
**Updated:** 2026-04-27 by cap-map-followups

Pursuit layer: commitment-to-completion arcs that span multiple engram firings. A Pursuit holds the dopamine-event lifecycle (commitment → subgoal → completion/abandonment) for actions that cannot be captured by a single engram.

Primary file: wild_igor/igor/cognition/pursuits.py — read its top-of-file docstring for the canonical explanation.

Gate: IGOR_PURSUITS_ENABLED (currently true on this host). When disabled, spawn() returns a no-op Pursuit with status=disabled.

MVP scope shipped: Pursuit dataclass + in-process registry, spawn/evaluate_completion/suspend/resume, dopamine-event subscriber hook.

Deferred: Postgres persistence, staleness-based abandonment, milieu integration, cascade-side awareness.

Design docs: lab/design_docs/pursuit_layer.md (concept and biology), lab/design_docs/pursuit_programming.md (when/how to wrap).
