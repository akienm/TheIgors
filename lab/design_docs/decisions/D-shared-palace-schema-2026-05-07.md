# D-shared-palace-schema-2026-05-07
**title:** Shared palace schema for 4-consumer agent layer (Akien/CC/Igor/Rack-Minion)
**date:** 2026-05-07
**status:** open
**spawned_tickets:** T-cc-palace-schema-design, T-cc-skills-triage, T-adc-summarizer-device

## Decision narrative
The palace must serve all four first-class consumers (Akien, CC, Igor, Rack-Minion) — not be CC-private. Schema: `palace.shared.*` for cross-agent context (Akien profile, rules, capabilities, audits); `palace.projects.*` for per-project context (summary/map/standards/decisions). Igor's TheIgors palace stays in TheIgors postgres and federates via a pointer node. SummarizerDevice lands in ADC first; Igor is a depth consumer (reads detail/chunks tier for nuanced reading), and composes downstream graph deposit separately.
