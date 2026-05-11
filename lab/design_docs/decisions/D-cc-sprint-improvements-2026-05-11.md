# D-cc-sprint-improvements-2026-05-11
**title:** Autonomous sprint loop + ultrathink plan review for CC sprinting
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-cc-autonomous-sprint-loop, T-sprint-ticket-ultrathink

## Decision narrative
Two sprint workflow improvements: (1) /sprint-loop skill uses ScheduleWakeup to keep sprinting a full queue autonomously — schedules its own next wakeup before starting the batch so compact mid-sprint does not lose the loop; terminates when queue is empty. Motivated by upcoming design-day queue fill. (2) Ultrathink added to sprint-ticket Step 4 for L/XL and HIGH-inertia tickets — forced deep plan review before coding on high-stakes work.
