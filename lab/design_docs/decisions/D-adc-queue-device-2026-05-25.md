# D-adc-queue-device-2026-05-25
**title:** Build ADC queue rack device as the canonical ticket queue — MCP interface, no claiming
**date:** 2026-05-25
**status:** open
**spawned_tickets:** T-adc-queue-device, T-adc-queue-no-claiming, T-query-ticket-mcp-switch, T-consequence-adc-queue-device

## Decision narrative
Build a queue rack device in UnseenUniversity (devices/queue/) that IS the work ticket queue. Every consumer — CC, Igor, Librarian — calls queue_next(worker) → ticket JSON or None via MCP. No claiming: queue_next is atomic (marks returned ticket in_progress in one DB operation). Backend: cc_queue.py's existing Postgres table. Alternative considered: keep cc_queue.py as the direct consumer interface (chose rack device because single MCP mechanism = one place to change, works across all consumers, aligns with the erector-set architecture).

## Hypothesis
mcp__datacenter__queue_next(worker="claude") is callable and returns a ticket from the existing queue; /query-ticket skill and context-load Step 5.95 use the MCP path; no direct cc_queue.py calls remain in skill files.

## Measurement Signal
queue_next() tool appears in datacenter_manifest; /query-ticket SKILL.md Step 1 calls mcp__datacenter__queue_next; cc_queue.py fallback reference removed from skill files.

## Goal Link
none: architectural infrastructure decision that enables the single-mechanism goal but is not directly a capability growth ticket.
