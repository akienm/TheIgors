# D-adc-shared-agent-substrate-2026-05-08
**title:** ADC as shared agent substrate — routing manifest + capability extraction
**date:** 2026-05-08
**status:** open
**spawned_tickets:** T-adc-routing-manifest, T-skill-capability-check-dynamic

## Decision narrative
ADC is the shared capability substrate for both CC and Igor — capabilities extracted into ADC devices are consumed via MCP by both agents identically, with no per-agent wiring. The key insight: "easier for CC is easier for Igor too" because they are both agents consuming ADC capabilities. The upgrade that enables this is an opinionated routing manifest: datacenter_manifest upgraded to return a task-shape → MCP tool map, so both CC (CAPABILITY CHECK step in sprint-ticket) and Igor (habit routing) pick the right tool without reasoning overhead or hardcoded heuristics. T-librarian-db-proxy (filed under D-librarian-rack-agent-2026-05-08) is the first concrete capability extraction that this manifest will surface.
