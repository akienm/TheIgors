# Cognition subsystem rules (loads when editing wild_igor/igor/cognition/ files)

## HIGH-inertia files in this directory
- `narrative_engine.py` — prompt construction; any change that grows context load needs budget review
- `coa.py` — main loop tick; threading changes need race-condition analysis

## Key invariants
- `_ne_worker()` in coa.py spawns ONE thread; never add a second ne_thread
- All DB writes from cognition modules use direct psycopg2 (not cortex.py)
- escalate_to_channel() is always the fallback — never go silent

## Current in-flight primitives (D-activate-primitive-2026-05-10)
activate() in activate.py → focus_state.py → propagates via interpretive_edges WITH RECURSIVE CTE
Proposals queue in proposals.py — dreaming/librarian PROPOSE, NE habits COMMIT
