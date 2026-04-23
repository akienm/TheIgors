# D-consult-primitive-2026-04-23

**title:** Unified consult primitive — peer-LLM consultation replaces handoff-shape escalation
**date:** 2026-04-23
**status:** open
**spawned_tickets:** T-consult-primitive, T-consult-prompts, T-consult-confab-scan, T-consult-pe-chain-wire, T-consult-reasoning-wire, T-consult-observe-and-tune

## Narrative

Two observed failure modes with the same structural cause: (1) reasoning-stuck turns where BG WINNOW fires with near-zero confidence and the LLM answers *as* Igor (handoff, voice loss, confabulation); (2) coding-stuck turns where pe_chain ESCALATES at SITUATE-returns-0 / preflight-red / implement-fails-twice with no recovery path.

Build a unified consult primitive: `ConsultSession` (stateful multi-turn) where Igor asks a peer-LLM "help me understand what's wrong — do not solve" and integrates returned hypotheses as TWM markers for the next reasoning step. Consult is conversation-shaped, not query/reply — Igor may follow up, reason over intermediate results, or conclude. Same primitive for reasoning and coding paths; prompt templates differ per problem kind.

No feature flag. Ship it, log every turn to ~/.TheIgors/local/logs/consults.log, and let T-consult-observe-and-tune trip when 50 turns have accumulated to review confidence threshold and call-site triggers.

Logs visible in console (igor.consult logger routes through igor.* hierarchy) but NOT broadcast to web channel — consults are Igor's internal scaffolding, the user sees only synthesized replies.
