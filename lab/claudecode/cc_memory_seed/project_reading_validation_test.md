---
name: Reading validation test — acceptance criteria for D126 + Watcher filter
description: 5 already-absorbed language books as the acceptance test for postgres stability + Watcher pre-filter extraction quality
type: project
---

The acceptance test for D126 (postgres/multi-box) + reading improvements:

## Test design
1. Pick 5 already-absorbed language books from the learn queue
2. Seed Watcher interest categories (language, neuroscience, programming, AI, etc.)
3. Add Watcher pre-filter to book_learner (keyword MVP, embedding upgrade later)
4. Re-run those 5 books through the learn queue
5. Count delta nodes — new memories extracted that weren't there before

## Interpretation
- New nodes appear → targeted extraction is working, multi-box pipeline stable
- No gains → something is wrong — investigate extraction, filter, or pipeline
- Investigation path → thread/trace debugging (habit activation traces through the matrix)

## Prerequisites (must be stable first)
1. D126 postgres migration complete + Igor running clean on two-channel
2. Reading across boxes stable (not strangling the DB)
3. Watcher categories seeded with real interests
4. Watcher pre-filter wired into book_learner

## Why these books
Already absorbed = delta nodes are purely from better extraction, not new content.
Language books = high-density domain Akien cares about = Watcher filter most likely to help.
Small set (5) = fast feedback loop without burning the full queue.

**Why:** This is the empirical validation of the whole substrate investment. If the filter + postgres + multi-box works, we see it here. If not, thread debugging (matrix trace visualization) becomes the next priority — which connects to the Process Development Tools debugger work.

**How to apply:** Don't start this test until multi-box reading is confirmed stable. This is the "did it all work?" moment, not an intermediate check.
