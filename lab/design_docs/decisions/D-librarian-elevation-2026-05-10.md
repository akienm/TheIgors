# D-librarian-elevation-2026-05-10
**title:** Retarget memory curation to ADC Librarian device; add focus quality tracking; wire Librarian MCP into CC
**date:** 2026-05-10
**status:** open
**spawned_tickets:** T-librarian-curation-tools, T-librarian-focus-quality-log, T-librarian-mcp-cc-wiring
**closes:** T-igor-memory-librarian

## Decision narrative
The Librarian device already exists in agent_datacenter as a standalone reasoner with MCP surface. Memory curation (which T-igor-memory-librarian tried to put inside Igor's cognition stack) belongs in the Librarian device: standalone, independently debuggable, no Igor brain overhead. Debug it there first, then migrate logic into Igor later if warranted. The proposals queue (T-igor-proposals-queue) is the clean interface — Librarian PROPOSES, Igor DECIDES. Additionally: wire the Librarian's existing research/summarize MCP tools into CC context-load and sprint-ticket; add a focus quality log to track which memories actually contribute to NE output (feeding curation priority).
