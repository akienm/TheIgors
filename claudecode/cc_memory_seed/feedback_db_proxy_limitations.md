---
name: db_proxy SQL translation limitations
description: db_proxy does blanket ?→%s translation which breaks PostgreSQL jsonb ? operator — must use jsonb_exists() instead
type: feedback
---

db_proxy does `sql.replace("?", "%s")` for psycopg2 parameter binding. PostgreSQL's jsonb key-exists operator `?` (e.g., `metadata ? 'trigger'`) gets translated to a parameter placeholder with no corresponding parameter → `IndexError: tuple index out of range` at runtime.

**Why:** Discovered when optimizing `get_habits()` in cortex.py to use `metadata ? 'trigger'` for GIN index use — caused boot crash on every Igor restart.

**How to apply:** Never use `?` as a PostgreSQL operator in any SQL that goes through db_proxy. Always use the function-form equivalent:
- `metadata ? 'key'` → `jsonb_exists(metadata, 'key')`
- `array ? element` → use array functions instead
