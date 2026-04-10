#!/usr/bin/env python3
"""
cc_mcp_server.py — MCP server for Claude Code self-compaction via tmux.

Exposes request_compaction(preserve_instructions: str) tool.
Tool injects /compact <payload> into the running Claude Code tmux session.

Session name read from CLAUDE_TMUX_SESSION env var (default: claude-main).

Usage:
  1. Start MCP server:
     CLAUDE_TMUX_SESSION=claude-main python3 claudecode/cc_mcp_server.py

  2. Register tool in Claude Code MCP config (see instructions below)

  3. From Claude Code, call via MCP: request_compaction("preserve: ...")
"""

import json
import os
import subprocess
import sys
from typing import Any

# ── Tool Definition ────────────────────────────────────────────────────────

TOOL_DEFINITION = {
    "name": "request_compaction",
    "description": (
        "Inject /compact command into the Claude Code tmux session. "
        "Compaction trims conversation context and preserves session state. "
        "Called by /savestate skill to trigger compaction automatically."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "preserve_instructions": {
                "type": "string",
                "description": (
                    "Preserve string to pass to /compact. "
                    "Format: 'preserve: session=YYYY-MM-DDx done: X. next: Y. in-flight: Z.'"
                ),
            }
        },
        "required": ["preserve_instructions"],
    },
}


def _escape_tmux_payload(payload: str) -> str:
    """
    Escape payload for tmux send-keys.
    Basic strategy: replace single quotes with '\'' (shell convention).
    """
    return payload.replace("'", "'\\''")


def request_compaction(preserve_instructions: str) -> dict[str, Any]:
    """
    Inject /compact into the Claude Code tmux session.

    Args:
        preserve_instructions: Preserve string for compaction

    Returns:
        dict with "status" and "message" keys
    """
    session = os.getenv("CLAUDE_TMUX_SESSION", "claude-main")
    try:
        # Build the command to inject
        escaped = _escape_tmux_payload(preserve_instructions)
        cmd = f"/compact {escaped}"

        # Inject via tmux send-keys
        subprocess.run(
            ["tmux", "send-keys", "-t", session, cmd, "Enter"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )

        return {
            "status": "success",
            "message": f"Compaction queued for session '{session}'",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": f"tmux timeout (session '{session}' not responsive)",
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"tmux error: {e.stderr or e.stdout or str(e)}",
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "tmux not found — install tmux to use compaction",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"request_compaction failed: {e}",
        }


# ── MCP Server Interface ───────────────────────────────────────────────────


def handle_list_tools() -> dict[str, Any]:
    """Return available tools."""
    return {
        "tools": [TOOL_DEFINITION],
    }


def handle_call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch tool calls."""
    if name == "request_compaction":
        preserve_instructions = arguments.get("preserve_instructions", "")
        result = request_compaction(preserve_instructions)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result["message"],
                }
            ],
            "isError": result["status"] == "error",
        }
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unknown tool: {name}",
                }
            ],
            "isError": True,
        }


def main() -> None:
    """
    MCP server main loop.

    Reads JSON-RPC requests from stdin, dispatches to handlers, writes responses to stdout.
    This is the standard stdio-based MCP protocol.
    """
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")

            response: dict[str, Any] = {}

            if method == "tools/list":
                response = handle_list_tools()
            elif method == "tools/call":
                response = handle_call_tool(
                    params.get("name", ""),
                    params.get("arguments", {}),
                )
            else:
                response = {
                    "error": f"Unknown method: {method}",
                }

            if req_id is not None:
                response["id"] = req_id

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            # Send error response
            error_response = {
                "error": f"JSON decode error: {e}",
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            # Log error and continue
            error_response = {
                "error": f"Unexpected error: {e}",
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
