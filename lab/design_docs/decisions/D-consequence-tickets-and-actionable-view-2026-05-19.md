# D-consequence-tickets-and-actionable-view-2026-05-19
**title:** Consequence-check tickets + actionable queue view for Akien
**date:** 2026-05-19
**status:** open
**spawned_tickets:** T-decided-consequence-ticket, T-queue-actionable-view

## Decision narrative
Two workflow hygiene improvements: (1) /decided auto-drafts a gated consequence-check follow-on ticket for any decision with M/L/XL tickets or MEDIUM+ inertia touches — the ticket carries predicted unintended effects + what to check + a gate condition, so consequence-checking becomes a first-class tracked item rather than an informal afterthought. (2) cc_queue.py list gets an --actionable flag that returns only tickets Akien can act on right now: status in {sprint, design, akien, awaiting_approval}, gate null or gate-ticket closed, worker≠igor. "Needs design, open questions, ideas" are all actionable-for-Akien.

Alternative considered: embedding consequence checks in day-close audit (no follow-through ticket, just a pass at close time) — rejected because it doesn't carry the prediction forward, requires Akien to re-derive context at check time, and can't be triaged or escalated like a ticket.

## Hypothesis
Every M/L/XL /decided includes a consequence-check ticket in the queue; `cc_queue.py list --actionable` returns only items Akien can act on now (excludes gated/igor-worker items).

## Measurement Signal
Next /decided on an M+ decision shows a consequence ticket with a gate set; running `list --actionable` on a mixed queue excludes gated and worker=igor items and includes design/akien-status tickets.

## Goal Link
none: direct workflow hygiene — reduces decision-loop dead zones and attention fragmentation across actionable vs blocked items.
