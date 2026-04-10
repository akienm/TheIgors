# Database Architecture Audit — 2026-03-19
**Author**: Senior DBA analysis session with Akien Maciain
**Scope**: TheIgors word graph + memory graph + working memory substrates

---

## Findings

### Word Graph (wg_cooccur)

| Metric | Value |
|---|---|
| Storage | Postgres + SQLite mirror |
| wg_cooccur rows | 29,324,450 |
| wg_word_lang rows (vocab) | 2,110,247 |
| wg_word_docs rows | 6,460,765 |
| DB size (SQLite) | 3.9GB |

**Problem**: wg_cooccur is a corpus co-occurrence matrix — answers "did these words appear near each other in text?" This is a document retrieval primitive (BM25/tf-idf), not a cognition primitive. The question we need answered is "are these concepts semantically similar?" — which is embedding proximity, not corpus statistics.

**Problem**: 2.1M vocab tokens includes every inflection, typo, and corpus artifact. Biology stores ~50K active lemma stems. Lemmatization would reduce to ~80K; co-occurrence pairs collapse from 29M to ~500K; storage from 3.9GB to ~60MB.

**Biological finding**: Aphasia research confirms vocabulary is NOT one unified structure. Domain-specific cortical maps (tools→motor cortex, faces→fusiform, places→parahippocampal) are physically separate. Bigrams/chunks are in a different system from unigrams (closer to procedural memory). The architecture should reflect this.

---

### Memory Graph (memories table)

| Metric | Value |
|---|---|
| Total rows | 296 |
| FACTUAL | 157 |
| INTERPRETIVE | 135 |
| PROCEDURAL | 4 |
| Live embeddings | 0 (memory_embeddings empty, memories.embedding all NULL) |
| Phase 2 cosine rerank | NOT RUNNING — no embeddings populated |

**Problem**: Four fundamentally different access patterns collapsed into one table with one search strategy:

| Memory type | Right access pattern | Current pattern |
|---|---|---|
| PROCEDURAL (habits) | Hash lookup by trigger key — O(1) | Full table LIKE scan |
| EPISODIC | Timestamp range query | Full table LIKE scan |
| FACTUAL | Semantic similarity | Full table LIKE scan (Phase 2 not firing) |
| INTERPRETIVE | Edge traversal from activated node | Full table LIKE scan |

**Problem**: Embeddings not populated. Phase 2 (cosine rerank) infrastructure exists but never runs. Every retrieval is a raw keyword scan.

---

### Working Memory (TWM + ring_memory)

| Metric | Value |
|---|---|
| TWM rows (live) | 0 |
| ring_memory rows (live) | 0 |

Both structures are correct in concept but incur a DB round-trip per push/pop. FIFO-50 = 50 items = Python deque. Should be in-process with background persistence flush.

---

### Spreading Activation

`interpretive_edges` has 135 entries and `interpretive_traverse()` implements BFS. However `cortex.search()` starts cold — no seeding from recently-activated nodes. Biology almost never does cold search; it walks from the currently-active cluster. This means every retrieval pays full search cost even when context is warm.

---

## Recommended Changes (in execution order)

### T-db-lemmatize (S-size)
Lemmatize vocabulary on ingest. stem/lemmatize at write time; store canonical form as primary key, inflection as variant. Shrinks 2.1M → ~80K. Precondition for all other word graph work. Igor **must be down** — replaces core word graph table.

### T-db-wg-replace-cooccur (L-size)
Replace wg_cooccur (corpus co-occurrence, 29M rows) with embedding-proximity edges (top-20 semantically similar words per word, computed from nomic-embed-text). Schema: `wg_edges(word_a, word_b, similarity REAL)`. 1.6M rows. Run as offline batch job on lemmatized vocab. Igor **must be down** for cutover.

### T-db-populate-embeddings (S-size)
Backfill `memory_embeddings` for all 296 existing memories. Add embedding write to `cortex.store()`. Phase 2 cosine rerank starts working. Can run **with Igor up** (background job).

### T-db-type-routing (M-size)
Add `trigger_key` indexed column to memories for PROCEDURAL type. Route cortex.search() by memory_type before searching: PROCEDURAL→key lookup, EPISODIC→timestamp range, FACTUAL→semantic search, INTERPRETIVE→edge traversal. Code change; hot-reload sufficient. **Igor up** for dev, hot-reload for deploy.

### T-db-spreading-activation (M-size)
Seed cortex.search() from recently-accessed memory IDs. Walk interpretive_edges by weight. Collect activated neighborhood. Rank within that set; cold search is fallback only. Connects to T-trails-infra (trail = activation path). **Igor up** — pure code change.

---

## Igor Downtime Required

| Ticket | Igor down? | Reason |
|---|---|---|
| T-db-lemmatize | YES | Replaces wg_word_lang table |
| T-db-wg-replace-cooccur | YES (cutover only) | Drops+replaces wg_cooccur |
| T-db-populate-embeddings | No | Background batch job |
| T-db-type-routing | No | Code + hot-reload |
| T-db-spreading-activation | No | Code + hot-reload |

---

## Pre-existing Audit Reports

- `audit_report_20260317.md` — prior session audit (moved from claudecode/)
