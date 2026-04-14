# encapsulation

**Path:** `theigors/architecture/principles/encapsulation`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

Each object owns everything about its structure. inference_gateway owns all inference routing decisions; db_proxy owns all connection lifecycle; cortex owns all memory operations. Don't reach across object boundaries to manipulate internals — the choke point exists for a reason.
