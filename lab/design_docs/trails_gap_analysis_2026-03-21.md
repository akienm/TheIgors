# T-trails-infra Gap Analysis — 2026-03-21e

**Status:** Design pass (CC + Igor)  
**Prereq:** trails_through_node, trail_gradient, hot_paths live in cortex  
**DB reality:** tails and traces tables are EMPTY — migration never ran `trail_id`/`sequence_pos` columns onto the live schema

---

## What the system currently has

### Two tables: `tails` and `traces`

**`tails`** — event log, one row per node-surfaced-per-search-call
```
id, node_id, weight (= relevance_score), recorded_at
-- MISSING in live DB: trail_id, sequence_pos
```

**`traces`** — static path record, one row per search() call
```
id (UUID), recorded_at, query (text, max 200), nodes (JSON blob)
```
`nodes` JSON: `[{node_id, relevance, memory_type, sequence_pos}]`

### Code-defined but DB-absent: `trail_id` + `sequence_pos`
`_record_tails()` tries to write `trail_id` and `sequence_pos` into tails.
The live DB never got the `ALTER TABLE` migration — those columns don't exist.
The INSERT silently fails because it catches bare `Exception`.  
**Result: tails and traces tables are both completely empty.** Nothing has ever been recorded.

### Methods that exist (but have no data to work on)
- `get_tail_heat(node_id)` — decayed sum of weights
- `trail_gradient(node_id)` — rising/flat/fading trend
- `trails_through_node(node_id)` — trails that passed through a node (needs `trail_id`)
- `hot_paths(since_hours)` — co-activated node pairs (needs `trail_id` JOIN)
- `get_recent_traces(limit)` — recent search traces for introspection
- `_apply_trail_training()` — Hebbian edge strengthening (IGOR_TRAIL_TRAINING_ENABLED=false)

---

## Gap #1: The migration didn't land — BLOCKING (fix first)

The `ALTER TABLE` for `trail_id` and `sequence_pos` is inside `_init_db()` but wrapped in bare `except` that swallows errors silently. The CREATE TABLE statement for new DBs includes those columns, but the live DB was created before those columns were added.

**Fix needed:** A named migration entry in `_migrations` that:
1. `ALTER TABLE tails ADD COLUMN trail_id TEXT DEFAULT NULL`
2. `ALTER TABLE tails ADD COLUMN sequence_pos INTEGER DEFAULT NULL`
3. Creates `idx_tails_trail`
4. Writes `'tails_trail_id_sequence_pos'` to `_migrations`

Until this lands, literally no trail data is being written. Every other trail feature is running on empty.

---

## Gap #2: No first-class Trail object

A trail is currently reconstructed on-the-fly by querying `tails` for all rows with a matching `trail_id`. There's no row that *is* the trail — no single thing you can point at and say "this is the reasoning event that produced this response."

What's missing:
```sql
CREATE TABLE trail_metadata (
    trail_id     TEXT PRIMARY KEY,  -- UUID, same as traces.id (join key!)
    recorded_at  TEXT NOT NULL,
    query        TEXT,
    source       TEXT,              -- 'search', 'embed_search', 'habit', etc.
    node_count   INTEGER,
    duration_ms  INTEGER,           -- how long search took
    outcome      TEXT,              -- 'answered', 'escalated', 'deferred', etc.
    thread_id    TEXT,              -- links to ring_memory.thread_id
    session_id   TEXT,              -- day-close linkage
    twm_obs_id   TEXT DEFAULT NULL  -- nullable FK → twm_observations.id
                                    -- set when a TWM attractor triggered this trail
)
```

### TWM join — clarified 2026-03-21 (Akien correction)

**Correct join shape:**
```
twm_observations.id
  → trail_metadata.twm_obs_id  (nullable FK — links the whole trail to the attractor that triggered it)
    → tails.trail_id           (many rows per trail; tails weights decay naturally)
```

**Key distinction:**
- **Trails don't fade** — `trail_metadata` rows are permanent records of reasoning events.
- **Tails do fade** — individual `tails` rows carry weights that decay over time.
- `twm_obs_id` belongs on `trail_metadata`, **not** on individual `tails` rows.

**Semantics:** When a TWM attractor fires and causes a memory search, that search spawns a trail.
`trail_metadata.twm_obs_id` records which attractor observation triggered it.
The tails are just the nodes activated in that trail — same as always, weights decay naturally.
The trail record itself is permanent.

Right now `traces.id` == the trail UUID that goes into `tails.trail_id`. That's the join key. But `traces` only stores query + nodes — it's missing: source, duration, outcome, thread linkage, and twm_obs_id.

---

## Gap #3: No cross-trail narrative

`hot_paths` finds co-activated pairs, but there's no way to ask:
- "What trails fired during this session?"
- "What was the reasoning path for the response at 21:01?"
- "Which trail led to the Hebbian edge between A and B?"

This requires `thread_id` on `trail_metadata` and an index on it.

---

## Gap #4: No outcome annotation

A trail ends when search() returns. But we don't record what happened after — did the response resolve the query? Did NE promote it? Did trail training strengthen an edge?

This is fine for now (nice-to-have), but is the missing piece before trail-based RED ALERT retrospective is useful.

---

## Gap #5: trail_hot_paths returns nothing (data vacuum + schema gap both)

`hot_paths()` does a self-join on `tails.trail_id`. With trail_id column missing AND table empty, it always returns `[]`. The tool works correctly — it just has nothing to work on.

---

## Proposed fix sequence

### Step 1 (blocking — do immediately): Apply the migration
Name: `tails_v2_trail_id_sequence_pos`

```sql
ALTER TABLE tails ADD COLUMN trail_id TEXT DEFAULT NULL;
ALTER TABLE tails ADD COLUMN sequence_pos INTEGER DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_tails_trail ON tails(trail_id) WHERE trail_id IS NOT NULL;
INSERT INTO _migrations (name, applied_at) VALUES ('tails_v2_trail_id_sequence_pos', datetime('now'));
```

Add a `_migrations` check at the top of `_init_db()` (or a dedicated `_run_migrations()` method) that runs named migrations idempotently. The current bare-try-ALTER pattern is too fragile.

### Step 2 (structural): Create `trail_metadata` table as the first-class object

`trail_metadata.trail_id` = `traces.id` (they were minted by the same UUID call). 
`_record_trace()` currently returns the trace_id. `search()` passes it to `_record_tails()` as `trail_id`. The join key is already there in the code — it just needs a home row.

Write `trail_metadata` row in `_record_trace()` at the same time as the `traces` row.
Include `twm_obs_id` as a nullable column — populated only when a TWM attractor observation
triggered the search (passed in from the TWM integration layer).

### Step 3 (observability): thread_id on trail_metadata

Pass `thread_id` from the search call context into `_record_trace()` → `trail_metadata`.
This is what connects a trail to a specific conversation turn.

### Step 4 (TWM integration): wire twm_obs_id through

When TWM fires an attractor and calls search(), pass the `twm_observations.id` into the
search call so it lands in `trail_metadata.twm_obs_id`. This is the only place the TWM↔trail
link is recorded — not on tails rows.

### Step 5 (enabled later): IGOR_TRAIL_TRAINING_ENABLED=true

Once step 1 lands and trails are actually recording, enable Hebbian training on a test session and observe whether hot_paths starts producing meaningful co-activation pairs.

---

## What trails would give us (once unblocked)

- **Introspection**: "Why did I surface that node?" — trace the trail backward
- **RED ALERT retrospective**: "What was I reasoning about when X happened?"
- **Hebbian edge growth**: which memory pairs strengthen through repeated co-activation
- **Session-level arc**: what did I reason about during this conversation? (thread_id join)
- **hot_paths as attention map**: what concepts co-fire most often → emergent attractor detection
- **TWM attribution**: which attractor triggered which reasoning trail (twm_obs_id join)

---

## Day-close notes

Consolidation loop behavior since restart (2026-03-21):
- Tails/traces empty — no trail data accumulated this session
- Hebbian training disabled (expected)
- trail_hot_paths returning empty (expected given above)
- `inspect_trail` working correctly on traces (returns traces even when tails empty)
- NE surprise fired on PROC_WG_PREPARSE_TUNING — wg preparse timing is shifting

Correction logged 2026-03-21 (Akien via CC): trails don't fade, tails do.
TWM join is on trail_metadata.twm_obs_id, not on tails rows. Table renamed from `trails`
to `trail_metadata` in this doc to match the corrected join target and reduce ambiguity.

Next session: migration first, then verify tails are actually being written.
