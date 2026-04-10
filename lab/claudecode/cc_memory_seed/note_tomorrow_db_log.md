---
name: Tomorrow DB log review
description: Check memory_ops.log for slow query patterns after T-cortex-258/258b fixes
type: project
---

Check `~/.TheIgors/logs/memory_ops.log` in tomorrow's deep dive.

**Why:** db_proxy slow query warnings (147-192ms) for `SELECT * FROM memories WHERE id IN (...)` observed 2026-03-15. Same genesis IDs fetched twice per turn. Fixes queued as T-cortex-258 (drop embedding blob) + T-cortex-258b (in-process cache).

**How to apply:** After Workers run those tasks, check memory_ops.log to confirm slow queries are gone. If still present, dig deeper into which call sites are double-fetching.

Log location: `~/.TheIgors/logs/memory_ops.log`
