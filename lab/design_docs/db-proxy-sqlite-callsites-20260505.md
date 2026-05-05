# SQLite-ism Callsite Inventory — 2026-05-05

Phase A output for T-db-proxy-sqlite-shim-retire. Complete enumeration of every SQLite-ism
in the codebase that routes through `db_proxy.py`'s translation shim. Phase B/C tickets
will migrate each file to native Postgres and delete the shim.

---

## Shim classes in db_proxy.py (targets for deletion)

| Symbol | Lines | Purpose |
|---|---|---|
| `_INSTR_RE` | ~404 | Regex to catch `INSTR(col, val)` and rewrite to `strpos()` |
| `_translate_insert_or_replace` | ~428 | Rewrites `INSERT OR REPLACE` → `INSERT INTO … ON CONFLICT DO UPDATE` |
| `_PGConnWrapper` | ~463 | Wraps psycopg2 conn; translates `?`→`%s`, intercepts PRAGMA, routes executescript |
| `_PGRowProxy` | ~609 | Row wrapper providing sqlite3-style dict+index access |
| `executescript` | ~491 | No-op (SQLite only) |
| PRAGMA no-op | ~503 | Silently drops any `PRAGMA` statement |
| `lastrowid` via LASTVAL() | ~564 | Returns `SELECT LASTVAL()` to emulate sqlite3's `cursor.lastrowid` |

---

## Callers by file

### 1. `lab/utility_closet/budget.py` (TRIVIAL — S)

| Line | Pattern | Migration |
|---|---|---|
| 249 | `INSERT OR REPLACE INTO budget_config (key, value) VALUES ('spending_cap_usd', ?)` | `INSERT INTO infra.budget_config … VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value` |

Schema: `infra.budget_config` — PRIMARY KEY (key). Confirmed live.

---

### 2. `wild_igor/igor/tools/notebook.py` (TRIVIAL — S)

| Lines | Pattern | Migration |
|---|---|---|
| 138–151 | `INSERT OR REPLACE INTO entries (id, title, source, content, embedding, tags, ingested_at, chunk_index, total_chunks) VALUES (?,×9)` | `ON CONFLICT (id) DO UPDATE SET …` with `%s` placeholders |

Schema: `entries.id` = TEXT PRIMARY KEY. Confirmed.

---

### 3. `wild_igor/igor/memory/pending_replies.py` (TRIVIAL — S)

| Lines | Pattern | Migration |
|---|---|---|
| 120–125 | `INSERT INTO pending_replies … VALUES (?, ?, ?, ?)` | Change `?` → `%s` |
| 126 | `row_id = cur.lastrowid` | Add `RETURNING id` to INSERT; `row_id = cur.fetchone()[0]` |

Schema: `instance.pending_replies.id` = integer SERIAL (nextval). Confirmed live.

---

### 4. `wild_igor/igor/main.py` (TRIVIAL — S)

| Lines | Pattern | Migration |
|---|---|---|
| 497–499 | `conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")` in try/except | Remove entire try/except block — PRAGMA is a no-op through shim; no equivalent needed in Postgres |

Note: `conn` is obtained from `self.cortex._db()` (PGDatabaseProxy), so this always routes through the shim's PRAGMA no-op. Safe to delete.

---

### 5. `wild_igor/igor/cognition/word_graph.py` (MEDIUM — M)

| Lines | Pattern | Migration |
|---|---|---|
| 287 | `INSERT OR REPLACE INTO wg_meta (key, value) VALUES ('word_count', ?)` | `ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value`, `%s` |
| 387, 399, 413, 425 | Already use `ON CONFLICT` syntax but still have `?` placeholders | Change `?` → `%s` |
| 464 | `INSERT OR IGNORE INTO wg_word_lang (word, lang) VALUES (?, ?)` | `ON CONFLICT DO NOTHING`, `%s` |
| 487 | `INSERT OR REPLACE INTO wg_idf (word, score) VALUES (?, ?)` | `ON CONFLICT (word) DO UPDATE SET score = EXCLUDED.score`, `%s` |
| 776, 810, 828, 845 | `INSTR(col, '__') = 0` | `strpos(col, '__') = 0` |
| 511, 519, 582, 585, 599, 779, 789, 809, 812, 830, 832, 845, 861, 918, 919 | `?` placeholders | `%s` |

Schema: `clan.wg_meta` PK(key), `clan.wg_idf` PK(word). Confirmed live.
Note: Lines 334–347 already use `strpos` in index creation — that area is partially migrated.

---

### 6. `wild_igor/igor/memory/cortex.py` (HIGH RISK — L/XL, surface to Akien first)

Total `?`-placeholder SQL lines: **129**

| Lines | Pattern | Migration |
|---|---|---|
| 1508/1514 | `INSERT OR REPLACE INTO memories … VALUES (?, ×22)` | `ON CONFLICT (id) DO UPDATE SET …` (22 columns), `%s` |
| 1637/1642 | `INSERT OR REPLACE INTO memories … VALUES (?, ×22)` executemany | Same — executemany with `%s` |
| 1319/1377/1400 | `INSERT OR IGNORE INTO _migrations` | `ON CONFLICT DO NOTHING`, `%s` |
| 3932–3947 | `_upsert_embedding` — already has PGDatabaseProxy ON CONFLICT branch + SQLite fallback | Remove else (SQLite) branch entirely |
| 4550 | `obs_id = cur.lastrowid` (twm_observations, integer SERIAL) | Add `RETURNING id`; `obs_id = cur.fetchone()[0]` |
| 5400 | `return cur.lastrowid` (interpretive_edges, integer SERIAL) | Add `RETURNING id`; `return cur.fetchone()[0]` |
| 5697 | `INSERT OR REPLACE INTO lists … VALUES (?, ×7)` | `ON CONFLICT (list_name, item_key, instance_id) DO UPDATE SET …`, `%s` |
| 1974/1977, 2076 | `json_extract(metadata, ?)` — **SQLite JSON, NO shim translation** | Investigate: these paths may be dead/broken on Postgres. Must audit before migrating. |
| 1953 (comment) | "Never use metadata ? 'key' — db_proxy translates ? → %s (breaks jsonb operator)" | Post-migration: JSONB `?` operator becomes safe once shim is deleted |
| All other `?` lines | ~129 total raw `?` placeholders | Mechanical `?` → `%s` sweep |

Schema: `clan.memories` PK(id TEXT), `clan.memory_embeddings` PK(memory_id), `clan.lists` PK(list_name, item_key, instance_id), `instance.twm_observations` integer SERIAL, `clan.interpretive_edges` integer SERIAL. All confirmed live.

**Risk note:** `json_extract` at lines 1974/1977/2076 has no db_proxy translation. Those paths are likely broken on Postgres today or dead code. Must grep call sites and test before migration to avoid silently breaking existing behavior.

---

## Files explicitly EXCLUDED

- `lab/utility_closet/redis_migrate_wg.py` — PRAGMA calls are on a **direct SQLite connection** (`PRAGMA journal_mode=WAL`, `PRAGMA cache_size`), NOT via db_proxy. This is intentional SQLite for a migration tool; skip.
- `lab/utility_closet/db_proxy.py` itself — target for deletion after all callers migrate (Phase B/C terminal ticket)

---

## Proposed Phase B/C ticket sequence

```
T-sqlite-out-main-pragma        (S)  — Remove PRAGMA block from main.py
T-sqlite-out-small-callers      (S)  — budget.py + notebook.py + pending_replies.py
T-sqlite-out-word-graph         (M)  — word_graph.py: INSTR→strpos, INSERT OR REPLACE→ON CONFLICT, ?→%s
T-sqlite-out-cortex             (L)  — cortex.py: 129 ?-lines + INSERT OR REPLACE + lastrowid + json_extract audit
T-db-proxy-shim-delete          (S)  — Delete shim classes from db_proxy.py (gated on all above)
```

All tickets share `decision_id` from the /decided filed against this inventory.
