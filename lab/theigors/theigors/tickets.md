# Tickets — cc_queue canonical storage

**Path:** `theigors/tickets`
**Updated:** 2026-04-20T19:24:46.162487+00:00 by migrate_tickets_to_palace

All tickets are FACTUAL memory rows with parent_id=TICKETS_ROOT. Individual ticket palace nodes under this path are stable pointers — mutable state (status/result/timestamps) lives only in clan.memories.

## Pointers

- `memories:TICKETS_ROOT`
