# D-announce-protocol-2026-05-01
**title:** Datacenter announces capabilities to plugged-in agents — protocol shape ratified
**date:** 2026-05-01
**status:** open
**spawned_tickets:** T-datacenter-capability-announce-protocol (parent), T-comms-device-router-mismatch, T-comms-lineage-alias-removal, slice1-children TBD

## Decision narrative
Akien reviewed Opus's announce-protocol design doc (lab/design_docs/announce-protocol-design-2026-05-01-opus-pass.md) and ratified all 11 open questions in § 14. Headline decisions:

1. Profile (static YAML, runtime dir) and Manifest (dynamic, derived) are sharply distinct
2. Single transport: IMAP envelopes on existing bus; surface adapters at each end
3. Suffix-style addresses (`comms://cc.0.console`) — zero router-change
4. Lineage form aliasing **NOT shipped** — accelerated deprecation per E-decision (single user, research project, "if it breaks we fix it")
5. Re-announce is push-on-change via `comms://announce-events` channel
6. Igor's system prompt gains BOUND CAPABILITIES layer with manifest etag in cache key
7. CC plugs in via new MCP server (`agent_datacenter/devices/claude/announce_mcp.py`)
8. Trust model unchanged: localhost-uid trust
9. `channel.py` becomes thin shim; sweep is child ticket
10. `cc_queue.py` orthogonal — tickets are state, not capabilities
11. Profile inheritance shipped in v1 (deep-merge with __replace__ marker)
12. Bootstrap minimum lives in the per-agent shim (not a separate `bootstrap.json`)
13. Read-and-remove inbox pattern; IMAP becomes pure delivery transport
14. Manifest persists with `stale_after_s ~5min` on agent side
15. Profiles: repo canonical (`agent_datacenter/config/profiles/`), runtime read (`~/.agent_datacenter/profiles/`)
16. CC palace permissions: `read_write` (Akien: "you're his doctor")
17. Cross-cutting: SQLite-removal has 3 outstanding tickets — separate decision cycle (resolved later as D-reorg-execute-2026-05-01)

This decision spans multiple slices. Slice 1 = round-trip vertical (envelope + profile + manifest + broker + igor profile + round-trip test). Subsequent slices add skeleton integration, live invalidation, agent-side clients, Igor cognition wiring, and cleanup.
