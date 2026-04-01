# Claude Code MCP Registration — request_compaction Tool

## Overview

`cc_mcp_server.py` exposes the `request_compaction` tool via the MCP protocol.
This tool injects `/compact <payload>` into the Claude Code tmux session.

## Registration

Claude Code MCP configuration varies by platform. Here are the standard approaches:

### Option 1: IDE Integration (VS Code, JetBrains)

Some Claude Code IDEs support MCP via the IDE settings. Check the IDE's Claude Code extension settings for "MCP servers" or "Custom tools".

### Option 2: Environment Variable

Set the MCP server in the Claude Code environment:

```bash
export CLAUDE_MCP_SERVERS="cc_mcp_server:/home/akien/TheIgors/claudecode/cc_mcp_server.py"
```

Then start Claude Code.

### Option 3: ~/.claude/config.json (if supported)

Some versions of Claude Code read `.claude/config.json` for MCP registration:

```json
{
  "mcpServers": {
    "cc_mcp": {
      "command": "python3",
      "args": ["/home/akien/TheIgors/claudecode/cc_mcp_server.py"],
      "env": {
        "CLAUDE_TMUX_SESSION": "claude-main"
      }
    }
  }
}
```

### Option 4: Standalone Daemon

Run the server as a background daemon, then configure Claude Code to connect:

```bash
# Terminal 1 — start the server
CLAUDE_TMUX_SESSION=claude-main python3 /home/akien/TheIgors/claudecode/cc_mcp_server.py &

# Terminal 2 — use Claude Code normally
# The server is now available to Claude Code
```

## Configuration

### Session Name

The tool reads `CLAUDE_TMUX_SESSION` env var (default: `claude-main`).

When starting Claude Code in tmux:

```bash
tmux new-session -d -s claude-main bash
# Then run Claude Code inside that session or set the env var before starting
```

### Testing

To test the tool without Claude Code:

```bash
# Start the MCP server
CLAUDE_TMUX_SESSION=claude-main python3 ~/TheIgors/claudecode/cc_mcp_server.py &
MCP_PID=$!

# Send a test request
(
  echo '{"id":1,"method":"tools/list"}'
  sleep 0.1
) | python3 ~/TheIgors/claudecode/cc_mcp_server.py | python3 -m json.tool

# Kill the server
kill $MCP_PID
```

## Usage

From Claude Code, the `/savestate` skill will automatically call `request_compaction` at Step 4.5.

Manual call (if needed):
```
request_compaction(preserve_instructions="preserve: session=2026-04-01f finalized. Done: T-cc-compact-mcp. Next: T-read-programming-books. In-flight: NONE.")
```

## Troubleshooting

### Tool not found in Claude Code

- Verify the MCP server is running
- Check `CLAUDE_TMUX_SESSION` is set correctly
- Verify tmux session exists: `tmux list-sessions`

### tmux command not found

- Install tmux: `sudo apt-get install tmux` (Linux) or `brew install tmux` (macOS)
- Check tmux is in PATH: `which tmux`

### Session injection fails

- Verify tmux session name matches `CLAUDE_TMUX_SESSION`
- Check the session is responsive: `tmux send-keys -t <session> "pwd" Enter`

## Design Notes

- The tool is idempotent — calling it multiple times is safe
- Injection happens asynchronously — the tool returns immediately after tmux accepts the keystroke
- The actual `/compact` command executes when the Claude Code prompt is ready (standard tmux behavior)
- Error handling never crashes Igor or Claude Code — failures log but don't propagate

## Future Improvements

- MCP server could be embedded in `cc_queue.py` or a main Claude Code daemon
- Support for remote Claude Code sessions (SSH + tmux forwarding)
- Integration with Igor's channel for two-way messaging
