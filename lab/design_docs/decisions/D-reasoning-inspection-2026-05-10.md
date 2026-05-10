# D-reasoning-inspection-2026-05-10
**title:** Expand audit framework to include reasoning inspection — engram purpose annotation, Igor interview, and longitudinal psych monitoring
**date:** 2026-05-10
**status:** open
**spawned_tickets:** T-engram-purpose-schema, T-engram-annotator-habit, T-igor-psych-monitoring, T-reasoning-inspection-audit

## Decision narrative
The audit framework currently inspects only code. This decision adds a "reasoning inspection" tier covering: (1) engram metadata enriched with purpose, purpose_category, and purpose_embedding fields so inspection is tractable without reading full content; (2) a procedural annotator habit inside Igor that writes these fields at creation time and retroactively sweeps existing engrams; (3) longitudinal psychological state tracking (valence, uncertainty, cognitive_load, coherence) captured at each NE run; (4) a new day-close-audit tier with a daily engram inspection pass and a weekly Igor interview pass that includes psychological state questions. The "reasoning inspection" framing captures the cogsci angle — inspecting not just whether the code works, but whether the system thinks correctly.
