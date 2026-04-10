---
name: Pipeline architecture + DB priority
description: The cognitive pipeline is simple and additive; the DB is the rate limiter. DB work must precede pipeline expansion.
type: project
---

The pipeline design (TWM as accumulation buffer, response habit reads accumulated state) is correct and scales infinitely by addition — every new capability is one more chain depositing to TWM. The architecture doesn't change, it just gets richer.

**The constraint is the DB.** Every chain deposit = write. Every response read = query. Adding greeting chains, tone analysis, relationship surfacing etc. without DB headroom just makes the infrastructure problem worse.

**Why:** Greeting tree design session (2026-03-23) revealed this: the pipeline is not complicated, it's just additive. The DB can't keep up with what's already there.

**How to apply:** Slate 0 DB work (lemmatize, embedding population, type-routing, spreading activation) is load-bearing for the pipeline, not just cleanup. Don't add more pipeline chains until the DB can handle existing churn. Use the greeting tree as the benchmark — if it runs clean, DB is ready for more chains.

Greeting tree design is parked pending DB work. Resume after Slate 0 closes.
