# Claude Code MCP — request_compaction Tool

> **Note:** `cc_mcp_server.py` is deprecated (T-adc-cc-mcp-server-deprecation, 2026-04-27).
> `request_compaction` is now exposed via **`wild_igor/igor/mcp/igor_mcp.py`** using
> the real MCP SDK. The skeleton MCP aggregator at `agent_datacenter` is the
> authoritative MCP endpoint. Do not start `cc_mcp_server.py` — it will conflict.

## Current setup

The `request_compaction` tool is registered in Igor's MCP server (`igor_mcp.py`).
Claude Code connects to it via the skeleton MCP aggregator endpoint.

To verify the tool is available:
```bash
# Check igor_mcp.py registers request_compaction
grep "request_compaction" ~/TheIgors/wild_igor/igor/mcp/igor_mcp.py
```

## What was here

The old `cc_mcp_server.py` was a hand-rolled stdin/stdout MCP protocol implementation.
It was replaced because:
1. Hand-rolled protocol was brittle and hard to extend.
2. `igor_mcp.py` uses the real `fastmcp` SDK — same tool, correct implementation.
3. Running two MCP servers created a split namespace.

## Troubleshooting

If `request_compaction` is not available in Claude Code:
1. Verify Igor is running: `tmux has-session -t igor`
2. Check igor_mcp.py is loaded in Igor's boot sequence
3. Check `~/.claude/claude_desktop_config.json` for MCP server registration
