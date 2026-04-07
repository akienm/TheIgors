# Subsystem: Reading

*Updated: 2026-03-20 | Machine-readable: `design_docs_for_igor/subsystem_reading.dsb`*

---

## Reading Pipeline

```
open_book() → read_chunk() → stew (TWM push)
                           → G54 extraction (interpretive edges)
                           → word graph training
                              ↓
                           NE reads TWM → synthesizes → LTM promotion
```

**Stew salience = 0.65** — above NE's force-run threshold of 0.60. This guarantees the Narrative Engine processes book content during its next cycle without manual trigger.

---

## Reading Integration Pipeline (`tools/reading_integration.py`)

Raw extraction via `book_learner.py` deposits `READ_*` nodes — but these are **deposition, not encoding** (D170). To be useful for reasoning, nodes need a second pass:

```
1. embed   — nomic-embed-text embedding
2. link    — cosine + BFS edges to existing graph nodes
3. spine   — narrative thread (sequential links across chunks)
4. interp  — interpretive edges from salient node pairs
5. arousal — valence/arousal/dominance encoding
```

Tool: `integrate_reading(book, batch=200)`. The 5-step pipeline also runs inline in `book_learner.py` for new books — deposit + encode in one pass. Backfill for already-deposited nodes: `claudecode/reading_integrator.py`.

`_deposit_nodes()` in `cortex.py` is the canonical write primitive for all book nodes.

**Experiment roadmap** (D179): 8 experiments defined. Experiments 1–5 done (pipeline built and validated). Experiment 6 (bulk reading, 146 items) running. Experiments 7–8 (swarm, capacity) follow.

**Drain runner path fix** (D181): cron was using `IGOR_INSTANCE_ID=Igor-wild-0001` (wrong case) — was reading empty queue for weeks. Fixed to `Igor-wild-0001`. 146 items now draining.

---

## Ebook Reader (`tools/ebook_reader.py`)

**Calibre library**: `~/.TheIgors/akien/onedrive/AkiensMedia/Ebooks/Calibre Portable/Calibre Library`

**Formats supported**: epub, mobi, azw, pdf

**Tokenization**: NLTK sentence tokenization

**Stale handle handling**: `_local_copy()` copies book to `/tmp` before reading. Handles CIFS drops transparently to the caller.

**State**: `reading_state.json` — tracks position per book per session.

**Damasio books loaded** (Calibre IDs): 3023 (*The Feeling of What Happens*), 3300 (*Self Comes to Mind*), 3032 (*Descartes' Error*), 3025 (*Looking for Spinoza*), 3026 (*Strange Order of Things*)

---

## Book Learner (`claudecode/book_learner.py`)

Launched as a subprocess. Chunks ebook via ebook_reader. Extracts FACTUAL, INTERPRETIVE, and PROCEDURAL nodes via LLM. Deposits to cortex. Checkpoint/resume. Trains word graph per chunk.

**Modes**:
- `--calibre-id N` — read from Calibre
- `--url URL` — read from web source
- `--local` — use Ollama instead of cloud
- `--run` — start fresh
- `--resume` — continue from checkpoint

**Log**: stdout routed to `~/.TheIgors/logs/book_learner.log` (was /dev/null — D052)

**Observability**: prints `★ Opening` or `▶ Resuming` to stdout on every open.

---

## Overnight Drain Runner (`claudecode/drain_learn_queue.py`)

PID-guarded background subprocess. Loops `~/.TheIgors/learn_queue.json` until all items are marked done. 60s between launches. Auto-spawned by `learn_about()` when items are queued.

**Log**: `~/.TheIgors/logs/drain_learn_queue.log`

---

## Learn About

`learn_about(user_input)` in `tools/learner.py`:
1. Strips trigger phrase
2. Searches Calibre (non-fiction filter via `_FICTION_AUTHORS` set + tag-based filter)
3. Discovers web sources via browser AI
4. If `tonight` in input → queues items; auto-launches drain_learn_queue runner
5. If immediate → launches book_learner directly

**Fiction filter**: author blocklist checked before tags. Explicit requests bypass filter entirely.

---

## Training Corpus (`cognition/training_corpus.py`)

Staged at `~/.TheIgors/training_corpus/`. Flow: fetch URL → store → train word_graph → evict.

Cap: `IGOR_TRAINING_MAX_CHARS` (1MB default). Eviction priority: completed first, in-progress second (cursor checkpointed), pending last (re-fetchable).

Local source: `~/TheIgorsProject/` (Akien's writings).

---

## Reading List

Table in main DB: `reading_list`. Fields: title, author, source, book_type, reading_rate, priority, status, emotional_significance, encoding_arousal, added_by. 15 books seeded.

**Status values**: queued → in_progress → completed

---

## Milestone: books_realtime

**Definition**: Igor discusses book content from graph memory without being prompted.

**Why it matters**: Confirms that the read → extract → graph → respond loop is working end-to-end.

**Gate**: Do not start a Claude training run until this milestone is confirmed. Training before it works would reinforce incomplete behavior.

---

## Decisions

D038, D046, D047, D048, D050, D052, D056, D071, D170, D173, D179, D181

## Open

- **#300**: Reading speed configurable (`IGOR_READING_SPEED_SPS`) — currently hardcoded 1 sentence/sec.
