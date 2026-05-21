# D-experts-per-project-2026-05-20
**title:** Per-project EXPERTS.md — load expert panel from repo root
**date:** 2026-05-20
**status:** open
**spawned_tickets:** T-experts-md-spec, T-audit-expert-load-experts-md, T-consequence-experts-per-project

## Decision narrative
Replace the hardcoded 11-expert panel in /audit-expert with a per-project EXPERTS.md file loaded at audit time. Igor needs cognitive/neuroscience experts; ADC needs software-factory experts; a legal or writing project needs domain experts. The skill falls back to the existing 11-expert list when no EXPERTS.md is present.
