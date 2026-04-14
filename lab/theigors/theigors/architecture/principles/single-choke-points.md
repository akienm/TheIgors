# single choke points

**Path:** `theigors/architecture/principles/single-choke-points`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

Cortex owns all memory r/w. Inference gateway owns all LLM calls. db_proxy owns all DB connections. Never bypass these layers — every observability, metrics, error handling, and rate limiting hook lives at the choke point. Bypassing means losing the hook silently.

## Pointers

- `wild_igor/igor/memory/cortex.py`
- `wild_igor/igor/cognition/inference_gateway.py`
- `wild_igor/igor/memory/db_proxy.py`
