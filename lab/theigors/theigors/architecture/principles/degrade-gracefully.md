# degrade gracefully

**Path:** `theigors/architecture/principles/degrade-gracefully`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

Any dependency failure (service down, DB unreachable, inference tier unavailable) triggers the habit chain for recovery + graceful tier fallback. Not special-case error handling — the same habit machinery that runs everything else. Recovery is just another thing Igor does, expressed in habits.

From D113 (now T-architecture-core-principles 2026-04-14).

## Pointers

- `wild_igor/igor/cognition/inference_gateway.py`
