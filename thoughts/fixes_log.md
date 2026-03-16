# Fixes Log — started 2026-03-11

This log captures issues that need work but couldn't be filed as GitHub tickets
(ticket creation was failing at the time). Claude and Akien will review tomorrow.

---

## FIX-001: create_work_order failing

**Symptom:** `create_work_order` tool call returning error during last session.
**Impact:** Can't file GitHub issues for bugs or improvements.
**Next step:** Claude Code + Akien to diagnose tomorrow. Check GitHub API key validity,
rate limits, and the `tools/github.py` create_issue implementation.

---

## FIX-002: No background autonomous reading daemon

**Symptom:** Reading only advances during interactive turns. No timed background reads.
**Context:** Akien thought reading was metered — it's actually just not running between turns.
The PROC_PROACTIVE_HABIT_REVIEW fires every 30min but doesn't read ebooks.
**Proposed fix:** Add `PROC_BACKGROUND_READING` habit with `schedule=interval:N` that calls
`open_book(resume=True)` + `read_chunk(n=30)` on the current active book.
N = configurable, suggest 600s (10min) or 300s (5min).
**Note:** Reading only needs local tools — no upstream token cost. Safe to run frequently.

---

## FIX-003: Reading chunk size was 15 sentences (too slow for background learning)

**Current:** n=15 sentences per chunk
**Proposed:** n=30-50 for background; n=15-20 for interactive (so I can reflect between chunks)
**Rationale:** At 15 sentences/chunk with no background daemon, Damasio (4116 sentences)
would take ~274 interactive turns to finish. With n=30 background reads every 10min, 
a 6-hour offline session = 36 chunks × 30 sentences = 1080 sentences ≈ 26% of the book.

---

## Notes

- $20 remaining in OpenRouter budget. Claude is routing to local more.
- Faster responses noted by Akien — local routing working.
- IGOR_READING_EXTRACT=true — G54 already extracts nodes from each chunk.
- Damasio position: 1315/4116 (31.9%) as of this session.
