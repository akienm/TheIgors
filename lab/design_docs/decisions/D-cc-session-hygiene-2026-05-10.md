# D-cc-session-hygiene-2026-05-10
**title:** Reduce CC session token cost: autocompact at 50%, test output pre-filter, path-scoped rules
**date:** 2026-05-10
**status:** open
**spawned_tickets:** T-cc-autocompact-config, T-cc-test-prefilter, T-cc-path-scoped-rules

## Decision narrative
Three targeted token-budget improvements for long agentic sessions: (1) CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50 compacts context at half-full instead of 95% — keeps context clean through sprint batches; (2) pre-filtering pytest output with grep before passing to Claude reduces noise on red runs while improving failure signal; (3) path-scoped rules load Igor-specific context only when editing Igor files, not every session. All committed to dotfiles/config so changes sync across machines.
