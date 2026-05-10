# Memory subsystem rules (loads when editing wild_igor/igor/memory/ files)

## Architecture
- clan.memories — cross-instance semantic graph; psycopg2 direct only
- clan.interpretive_edges — graph edges (source_id, target_id, weight, relation)
- instance.* — per-instance tables (ring_memory, twm_observations, watch_problems, proposals, focus_state)

## HIGH-inertia files in this directory
- `cortex.py` — PRIMARY access layer; do not add new direct-DB code here (use psycopg2 modules)
- `models.py` — Memory schema definitions; adding fields requires migration + backward-compat check

## Key invariants
- Never hard-delete from clan.memories; use archived/soft-delete pattern
- purpose_annotator.py runs after each NE cycle; batch_size=2 to stay within budget
