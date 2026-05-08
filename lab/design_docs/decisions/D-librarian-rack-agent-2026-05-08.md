# D-librarian-rack-agent-2026-05-08
**title:** The Librarian replaces rack-minion — always-on rack agent with MCP, inference, DB proxy
**date:** 2026-05-08
**status:** open
**spawned_tickets:** T-librarian-device, T-librarian-mcp-tools, T-librarian-db-proxy, T-librarian-inference-routing, T-librarian-model-selection-skill, T-librarian-research-capability, T-igor-mcp-deprecate, T-claude-json-mcp-update

## Decision narrative
Rename/expand the rack-minion concept into "the Librarian" — a Discworld-themed always-on rack agent (OOK = 'Ook.'). The Librarian is a BaseDevice subclass in ADC. CC connects to it via MCP (stdio); the Librarian's backend speaks comms:// over the IMAP bus. Responsibilities: MCP tool surface (porting igor_mcp.py inventory), DB proxy (direct Postgres for sync MCP path, bus for async fire-and-forget), inference routing (Qwen 8B default; escalation tiers for research/summarization; cloud escalation for complex reasoning), research and summarization workflows, multi-interface (MCP, IMAP/bus, web channel). igor_mcp.py and cc_mcp_server.py deprecated once Librarian is live.
