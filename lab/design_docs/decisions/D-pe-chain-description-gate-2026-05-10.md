# D-pe-chain-description-gate-2026-05-10
**title:** Abort pe_chain early when ticket description is absent — stop SITUATE from inferring scope from title semantics
**date:** 2026-05-10
**status:** open
**spawned_tickets:** T-pe-read-ticket-description-gate

## Decision narrative
pe_chain's SITUATE step infers HIGH-inertia files from title semantics when description is absent, hands that code to HYPOTHESIZE via OBSERVE, and a hallucinated scope edit fires. The scope guard catches it after 0 attempts but the 5-week recurring pattern shows guards alone aren't enough. Fix: pe_read_ticket aborts with basket[error] when description is missing/title-only, before SITUATE runs.
