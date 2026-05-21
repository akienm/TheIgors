# D-queue-encapsulation-2026-05-21
**title:** Queue as encapsulated black box — dispatch IS assignment; workers request work, never see or select from queue directly
**date:** 2026-05-21
**status:** open
**spawned_tickets:** T-gate-date-parsing, T-dispatch-is-assignment, T-goal-37-task-service, T-consequence-skill-telemetry-repair, T-consequence-queue-encapsulation

## Decision narrative
The queue is an encapsulated service. Workers (Igor, CC) have exactly one operation: request_work(). The act of dispatch IS the assignment — no separate claim step. Follows the same encapsulation principle as the DB proxy and inference proxy. Motivated by overnight failures where _gate_clear's ticket-ID-only logic accidentally cleared a date-gated ticket, letting Igor sprint it early and write a wrong result.

## Hypothesis
Igor never sprints a ticket that wasn't dispatched to him, and never bypasses a date gate.

## Measurement Signal
24h channel log shows zero sprint-timeout events on already-closed tickets; _gate_clear correctly blocks date-gated tickets (confirmed via cc_queue.py list --gated).

## Goal Link
1.5a (Igor processes tickets reliably) + new Goal 3.7 (shared task management service for multi-agent ADC).
