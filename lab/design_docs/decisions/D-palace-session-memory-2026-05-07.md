# D-palace-session-memory-2026-05-07

**title:** Palace as primary agent-layer store for session context, transcripts, and day summaries
**date:** 2026-05-07
**status:** open
**spawned_tickets:** T-adc-palace-bootstrap, T-adc-palace-seed-decisions, T-adc-palace-session-writer, T-adc-palace-day-writer, T-adc-context-load-palace

## Decision narrative

The palace DB (not flat files) is the canonical store for all agent-readable context — including
session records, stripped transcripts, and day summaries. Flat files are echoes for human reading
and disaster recovery (structured enough to reconstruct from, not the read path for agents).

Three new palace namespaces: palace.sessions.* (one node per CC session, written at savestate),
palace.transcripts.* (session JSONL filtered to text-only — no tool calls — written at savestate),
palace.days.* (day roll-up of session summaries, written at day-close).

The session/transcript layer directly addresses the "getting lost after compaction" problem:
CC reads palace.days.* (last 10) at context-load to reconstruct recent history in minimal tokens.
Stripped transcripts are the drill-down layer — the WHY behind decisions — accessible via
palace.sessions.* → palace.transcripts.* pointer when the session summary points there.

Tickets discussed_at timestamps in metadata enable tracing a ticket back to the conversation
that produced it without reading the full transcript.

## Alternatives considered

- Flat files as primary: rejected — not searchable, requires CC to parse file paths, no structured
  drill-down from summary to transcript
- No session records: rejected — CC loses context between compactions with no recovery path
  shorter than re-reading the git log

## Constraints

- Palace bootstrap (T-adc-palace-bootstrap) must exist before any of the writers can run
- Igor's palace stays separate; this palace is ADC-owned
