#!/usr/bin/env python3
"""
datacenter_mcp.py — MCP server exposing the announce protocol to Claude Code.

Wraps agent_datacenter.announce.AnnounceMcpServer and registers its three
methods as MCP tools so a CC session can announce itself, read its
manifest, and react to invalidates from inside Claude Code.

Tools:
  - datacenter_announce              : post identity envelope, cache manifest
  - datacenter_manifest              : return the cached manifest
  - datacenter_check_for_invalidate  : drain comms://invalidate, re-announce on match

Transport: stdio (Claude Code MCP standard)
Identity:  agent_id="cc", instance="{box}-{pid}", surfaces=["console", "mcp"]
           (defaults from AnnounceMcpServer; can be overridden via env vars
           CC_AGENT_ID, CC_INSTANCE_ID, CC_BOX_N).

Usage — already wired in /home/akien/TheIgors/.mcp.json. To launch standalone:
  python3 /home/akien/TheIgors/lab/claudecode/datacenter_mcp.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("datacenter_mcp")

# ── Singleton adapter (created lazily so import-time failures don't kill MCP) ─

_ADAPTER = None


def _adapter():
    """Lazy-construct the AnnounceMcpServer singleton."""
    global _ADAPTER
    if _ADAPTER is None:
        from agent_datacenter.announce import AnnounceMcpServer

        _ADAPTER = AnnounceMcpServer(
            agent_id=os.environ.get("CC_AGENT_ID", "cc"),
            instance_id=os.environ.get("CC_INSTANCE_ID"),
            box_n=int(os.environ.get("CC_BOX_N", "0")),
        )
    return _ADAPTER


server = Server("datacenter")


# ── Tool registry ─────────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="datacenter_announce",
            description=(
                "Post this CC session's IdentityEnvelope to comms://announce "
                "and wait for the broker's Manifest reply. Caches the manifest "
                "for subsequent datacenter_manifest calls."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "number",
                        "description": "Seconds to wait for reply (default 5.0)",
                    }
                },
            },
        ),
        types.Tool(
            name="datacenter_manifest",
            description=(
                "Return the cached announce-protocol Manifest dict. "
                "Returns {manifest: null} if datacenter_announce hasn't run."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="datacenter_check_for_invalidate",
            description=(
                "Drain comms://invalidate. If any envelope's target matches "
                "this client's agent_id (or 'registry'), re-announce and "
                "replace the cached manifest atomically. Returns count handled."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "reannounce_timeout": {
                        "type": "number",
                        "description": "Seconds for re-announce poll (default 5.0)",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = _dispatch(name, arguments or {})
    except Exception as exc:
        log.warning("datacenter_mcp dispatch failed for %s: %s", name, exc)
        result = {"ok": False, "error": f"dispatch error: {exc}"}
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]


def _dispatch(name: str, args: dict) -> dict:
    adapter = _adapter()
    if name == "datacenter_announce":
        return adapter.announce_tool(timeout=args.get("timeout", 5.0))
    if name == "datacenter_manifest":
        return adapter.manifest_tool()
    if name == "datacenter_check_for_invalidate":
        return adapter.check_for_invalidate_tool(
            reannounce_timeout=args.get("reannounce_timeout", 5.0)
        )
    return {"ok": False, "error": f"unknown tool: {name}"}


# ── Entry point ───────────────────────────────────────────────────────────────


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
