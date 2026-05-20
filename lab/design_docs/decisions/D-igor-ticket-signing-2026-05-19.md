# D-igor-ticket-signing-2026-05-19
**title:** Scraps rack gatekeeper + ticket created_by attribution
**date:** 2026-05-19
**status:** open
**spawned_tickets:** T-scraps-device, T-ticket-created-by, T-cc-queue-scraps-gate

## Decision narrative
Igor files placeholder tickets with no body (T-claude-1: "HIGH work", T-nw-1: "legacy ticket") that waste sprint cycles and are unattributable. Build Scraps — a new rack device in agent_datacenter named after one of the Igors' dogs — as a queue gatekeeper that validates ticket content before state transitions. Rule-based V1 with optional Qwen 8 (via InferenceDevice) for fuzzy usefulness check. Passing tickets get a `scraps_validated` sign-off stamp. Separately, add `created_by` field to ticket schema with auto-injection at the filing source.

Alternative considered: inline validation in cc_queue.py — rejected because it embeds gatekeeper logic in a tool rather than a composable rack device.

## Hypothesis
Every Igor-created ticket in the queue shows `created_by: igor`; Scraps blocks empty/placeholder tickets at add/claim time and signs off on valid ones.

## Measurement Signal
`cc_queue.py claim` on an empty-body ticket returns a Scraps issue list and aborts; `cc_queue.py show` on a valid ticket displays `scraps_validated` timestamp. Day-close shows 0 thin tickets filed by Igor.

## Goal Link
G-system-self-improvement
