# Igor Execution Constraints

**Path:** `theigors/rules/igor-constraints`
**Updated:** 2026-04-12T15:55:13.184913+00:00 by seed_memory_palace

Igor NEVER calls Anthropic direct (tier 5 inhibited). Use Igor's systems (gateway, router, logging) — never bypass. code_ref habits only dispatch 1-required-arg tools. identity_gate fires on read_file output. New tools must be added to tools/__init__.py.

## Pointers

- **file:** `wild_igor/igor/tools/__init__.py`
- **file:** `wild_igor/igor/cognition/inference_gateway.py`
