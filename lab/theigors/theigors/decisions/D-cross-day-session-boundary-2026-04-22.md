# D-cross-day-session-boundary-2026-04-22 — cross-day session boundary handling

**Path:** `theigors/decisions/D-cross-day-session-boundary-2026-04-22`
**Updated:** 2026-04-22 by D-cross-day-session-boundary-2026-04-22

Cross-day CC session boundaries need handling in two places:

1. Workflow: first user message on a new calendar day prompts /day-close for previous day if it has open items (soft prompt, not gate) — T-first-msg-of-day-close-prompt
2. Data: export_chat.py must route each message to its own day-file based on that message's own timestamp, so long-lived sessions that span days don't dump all content into one day-file — T-export-chat-per-message-date-routing

Context: 2026-04-22 chat log investigation revealed session 86b1b97d (started 2026-04-18, still active) dumping entire 4-day content into 2026-04-22.md because _date_for_transcript reads only first-line timestamp and falls back to mtime when first line is permission-mode/file-history-snapshot (no ts). Also symptom: 2026-04-18.md bloated to 297MB from repeated --all runs.

spawned_tickets: T-first-msg-of-day-close-prompt, T-export-chat-per-message-date-routing
date: 2026-04-22
status: open

