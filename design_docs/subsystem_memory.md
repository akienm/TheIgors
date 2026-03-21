# Subsystem: Memory

*Updated: 2026-03-20 | Machine-readable: `design_docs_for_igor/subsystem_memory.dsb`*

---

## Design Principles

- **Everything is memory.** No special cases. Habits, values, episodic experiences, factual knowledge — all live in the same graph.
- **All reads and writes go through Cortex only.** Reasoners and tools never touch raw SQL. Cortex is the single gatekeeper.
- **DatabaseProxy wraps every connection.** Timing, metrics, reconnect on failure. commit() on success, rollback() on exception.
- **Inertia is computed, not stored.** Formula: `base(type) + 0.1·log1p(activation) + 0.05·len(children) + 0.02·depth`. Emerges from use.

---

## Memory Types

| Type | Description |
|------|-------------|
| ROOT | Single root node; anchor for the entire graph |
| CP (Core Pattern) | CP1-CP6; structural bedrock; inertia 0.90+ |
| ID (Identity) | Who Igor is; role, character, inheritance |
| RM (Role Model) | Granny Weatherwax, Vetinari, Ankh-Morpork Igor, Akien |
| PROCEDURAL | Habits and learned action patterns |
| EPISODIC | This-session events; not portable; instance-local |
| INTERPRETIVE | Meaning-bearing edges; 4-part directed structure |
| EXPERIENTIAL | Internal states; what Igor noticed |
| FACTUAL | External facts absorbed from reading or conversation |

---

## Graph Structure

```
ROOT
 └── CP1-CP6   (inertia 0.90+ — never casually modified)
      └── ID1-ID14
           └── RM1-RM4
                └── PROC, EPISODIC, FACTUAL, INTERPRETIVE, EXPERIENTIAL
```

Graph depth drives inertia. The deeper and more connected a node, the harder it is to change. This is intentional: CP nodes should resist modification; ephemeral EPISODICs should not.

---

## Key Tables

| Table | Purpose |
|-------|---------|
| `memories` | Main graph: narrative, type, parent/children, VAD, inertia, embedding, metadata |
| `ring_memory` | FIFO-50 session context; injected into every API call |
| `twm_observations` | Transient Working Memory; push-only; TTL-gated |
| `interpretive_edges` | 4-part directed edges: direction, condition, meaning_payload, action_pointer |
| `tails` | Activation heat trail: node_id, weight, recorded_at, trail_id, sequence_pos |
| `word_graph` | Separate DB (`~/.TheIgors/word_graph.db`); nodes + edges + bigrams |

Works with both SQLite (default) and Postgres (`IGOR_HOME_DB_URL=postgresql://...`). Postgres schema auto-initialized via `_init_pg_schema()` on first boot.

---

## Key Methods

| Method | What it does |
|--------|-------------|
| `cortex.store()` | Write memory; increments activation |
| `cortex.search(query)` | Phase 1 text → Phase 2 cosine rerank; returns ranked list |
| `cortex.recall(id)` | Fetch by ID; increments activation |
| `cortex.twm_push(...)` | Deposit to TWM with salience, urgency, TTL |
| `cortex.ring_push(...)` | Append to ring; FIFO evicts oldest |
| `cortex.get_portable()` | Export: excludes EPISODIC, CREDENTIAL_REF, portable=False |
| `cortex.interpretive_traverse(seed_id)` | BFS from seed via interpretive edges |
| `cortex.expand_blob_memories(memories)` | Append blob content for relevance ≥ 0.5 |
| `db_proxy.get_metrics()` | Latency p50/p95/p99, slow count, error count |

---

## TWM (Transient Working Memory)

Push-only sandbox. Multiple sources deposit observations (reading stew, NE action impulses, threshold alerts, user input, etc.). The Narrative Engine reads and integrates. TTL cleans up expired entries automatically.

**Urgency** is orthogonal to salience. `urgency × salience` sorts the NE processing queue. Urgency ≥ 0.7 is flagged distinctly when context is built for the LLM.

---

## Portability

`Memory.portable = True` means the memory can be exported to other Igor instances. `portable = False` = instance-local (machine paths, episodic events, credentials). `CREDENTIAL_REF` type stores pointer only — never the credential value.

---

## Trails (`tails` table)

Every `cortex.search()` call records a trail — a timestamped activation sequence grouped by a UUID (`trail_id`). `sequence_pos` tracks traversal order within a trail.

This gives Igor a biological analog to neural activation patterns: the `tails` table IS the gradient signal. Co-activation heat → Hebbian edge strengthening → graph becomes smarter from use.

Tools:
- `inspect_trail(node_id)` — what trails activated this node, and when
- `trail_hot_paths(since_hours)` — most frequently co-activated node pairs

MCP tools available for CC sessions: `tail_heat`, `traces_recent`, `traces_get`, `hot_nodes`.

---

## Memory Sync (`tools/memory_sync.py`)

Hub-and-spoke swarm sync. Each box holds a full Postgres replica. Bidirectional via `GREATEST(activation_count)` — most-activated version wins.

Gate: `IGOR_SWARM_DB` (absent = sync disabled). Tool: `sync_memories(full="false")`. Habit: `PROC_MEMORY_SYNC` runs every 6h. `full=true` bootstraps a new box.

---

## Genesis

44 seed memories verified at boot: 1 ROOT + 6 CP + 14 ID + 4 RM + 10 PROC (genesis) + 9 new PROC. Guard checks for ROOT node existence (changed from `total_count==44` for Postgres compatibility). CP1-CP6 narratives verified against `GENESIS_CP_NARRATIVES` dict.

---

## Decisions

D001, D004, D005, D010, D013, D017, D027, D028, D039, D043, D045, D163, D169, D171, D174
