# D-uu-launcher-config-2026-05-28
**title:** UU zero-config launcher UX + config layout + configurable frontend shim
**date:** 2026-05-28
**status:** open
**spawned_tickets:** T-uu-config-layout, T-uu-librarian-chat, T-consequence-uu-launcher
**goal_link:** none: make UU accessible to non-technical users; zero-config startup
**concept_links:** none

## Decision narrative
Three entry points at repo root (./igor, ./superclaude, ./uu) — clone, run, works. All internals hidden except elevation/install prompts. Config layout: ~/.UnseenUniversity/uu.cfg (global defaults) + per-device config.cfg (replaces env vars). Flat layout, no intermediate rack folder. ./uu launches a Librarian chat interface via a configurable frontend shim (terminal|web, driven by config) — leverages an existing open-source terminal chat library rather than building new UI. Any agent gets the same console by changing shim config.

## Hypothesis
A non-technical user can clone the repo, run ./igor or ./uu, and have a working session without manual configuration.

## Measurement Signal
Fresh-clone test completes without requiring env var setup or manual config.

## Goal Link
none: make UU accessible to non-technical users; zero-config startup

## Alternatives considered
- Keep current env var complexity (chose config.cfg — debuggable, committable, human-readable)
- Build bespoke chat UI (chose existing library — don't build what already exists)
- Intermediate rack01 folder (chose flat — no multi-rack need yet, simpler paths)
