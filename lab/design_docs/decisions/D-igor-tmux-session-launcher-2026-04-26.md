# D-igor-tmux-session-launcher-2026-04-26

**title:** Igor launcher wraps itself in named tmux session

**date:** 2026-04-26

**status:** open

**spawned_tickets:** T-igor-tmux-session-launcher

## Decision narrative

Igor launcher (TheIgors/igor) now wraps itself in a named tmux session (IGOR_TMUX_SESSION, default: igor) so that terminal disconnect or close doesn't kill the restart loop mid-run. If already inside tmux, execs directly (no double-wrap). Committed in ea0cba88. Ticket is a traceability backfill.
