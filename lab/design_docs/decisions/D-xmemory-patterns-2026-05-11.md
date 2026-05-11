# D-xmemory-patterns-2026-05-11
**title:** xMemory paper — three implementable patterns for Igor memory architecture
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-igor-uncertainty-gated-recall, T-igor-memory-decay-dreaming, T-igor-consolidation-theme-palace

## Decision narrative
The xMemory paper (VentureBeat, 2026-05) describes a four-level memory hierarchy (messages→episodes→semantics→themes) with Uncertainty Gating as the key retrieval innovation. Three patterns map directly to Igor gaps: (1) Igor's activate.py uses pure similarity with no uncertainty signal — add conditional trace-level expansion when top-K confidence is low; (2) clan.memories has last_activated_at + activation_score but no lifecycle decay — add archive pass in dreaming.py for stale low-activation memories; (3) consolidation.py produces high-importance patterns but never promotes them to palace theme nodes — the "themes" level that xMemory says is what enables fast top-down retrieval.
