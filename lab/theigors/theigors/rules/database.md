# Database Rules

**Path:** `theigors/rules/database`
**Updated:** 2026-04-12T15:55:13.184913+00:00 by seed_memory_palace

NO SQLITE anywhere — everything Postgres. db_proxy translates ?→%s blanket, so use jsonb_exists(metadata, 'key') not metadata ? 'key'. All DB access through db_proxy, never raw psycopg2 in tools.

## Pointers

- **file:** `wild_igor/igor/memory/db_proxy.py`
- **table:** `Igor-wild-0001 (Postgres)`
