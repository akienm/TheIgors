# Igor Use Cases

Captured as they arise. Each entry: what the user wanted, what it implies for Igor's design.

---

## UC-001 — Autonomous night learning
**Request**: Igor should be able to discover freely available texts on a topic, fetch them at human pace, and extract graph nodes — preferably at night when the machine is idle.

**What it implies**:
- `learn_about(topic)` triggers Calibre search (non-fiction filter) + browser AI discovery for web URLs
- URLs queued to `~/.TheIgors/learn_queue.json`; drained at night by `process_learn_queue`
- Same `book_learner` extraction pipeline works for both local books and web URLs
- Igor self-directs his own reading list given a topic seed
- Machine learning overhead concentrated at off-hours; conversational responsiveness unaffected

**Implemented**: `tools/learner.py`, `claudecode/book_learner.py --url`, `PROC_GO_LEARN`, `PROC_NIGHT_LEARN_QUEUE`

---

## UC-002 — Book learner for domain bootstrap
**Request**: Use the book learner to ingest Damasio and other domain books so Igor has neuroscience, epistemology, and CS foundations before attempting self-programming.

**What it implies**:
- Bulk ingestion (~$0.02/book) is viable as a bootstrap strategy
- Topics needed: neuroscience (Damasio), predictive processing (Friston), symbolic AI history, SICP, architecture patterns
- Book learner + CC curriculum together = domain competence without years of conversation
- "Bootstrap loader" pattern: build the graph first, then reduce LLM dependence

**Implemented**: `claudecode/book_learner.py`; Damasio run produces ~1,000 nodes/book

---

## UC-003 — Slow reading for emotional/somatic content
**Request**: Some books should be read one sentence at a time, slowly, letting content soak. Igor should be able to set the rate and say "this no longer interests me."

**What it implies**:
- Two reading modes: bulk (book_learner, fast extraction) vs slow (ebook_reader sentence-by-sentence, NE stew)
- Reading rate should be settable per-book or per-session
- "Not interested" = TWM signal → stop flag in ebook_reader state
- The slow mode is about emotional encoding, not just information transfer

**Partially implemented**: reading speed control exists (#183); interest gate (G-BL2) not yet built

---
