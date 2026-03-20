#!/usr/bin/env python3
"""
igor_mcp.py — MCP server exposing Igor's Postgres DB to Claude Code.

Provides structured tool access to:
  - memories: search, get by id, list by type
  - traces: recent search traces (what nodes activated, in what order)
  - tails: decaying activation heat per node
  - turn_trace: per-turn reasoning log (thalamus/BG/habit/tier)
  - cc_send: inject a message into Igor's reasoning pipeline
  - wg_edges: node neighbors and edge weights

Transport: stdio (Claude Code MCP standard)
DB: Postgres at IGOR_HOME_DB_URL or hardcoded fallback

Usage — add to Claude Code settings:
  {
    "mcpServers": {
      "igor": {
        "command": "/home/akien/TheIgors/venv/bin/python",
        "args": ["/home/akien/TheIgors/claudecode/igor_mcp.py"]
      }
    }
  }
"""

import asyncio
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ── Config ────────────────────────────────────────────────────────────────────

PG_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)
TURN_TRACE_LOG = Path.home() / ".TheIgors" / "logs" / "turn_trace.20260319.log"
CC_SEND_URL = "https://localhost:8080/api/cc_send"

server = Server("igor")


# ── DB helper ─────────────────────────────────────────────────────────────────


def _pg():
    return psycopg2.connect(PG_URL)


def _q(sql: str, params=()) -> list[dict]:
    with _pg() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def _exec(sql: str, params=()) -> int:
    with _pg() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount


# ── Tool registry ─────────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="memory_search",
            description=(
                "Full-text search over Igor's memory graph. "
                "Returns top matches by narrative keyword overlap. "
                "Optionally filter by memory_type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search terms"},
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Filter by type: FACTUAL|INTERPRETIVE|PROCEDURAL|EPISODIC|EXPERIENTIAL|IDENTITY|ROOT|CORE_PATTERN (optional)",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="memory_get",
            description="Get a single memory node by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "Memory node ID"},
                },
                "required": ["memory_id"],
            },
        ),
        types.Tool(
            name="memory_list_by_type",
            description="List recent memories of a specific type, ordered by activation_count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "description": "FACTUAL|INTERPRETIVE|PROCEDURAL|EPISODIC|etc.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 20)",
                    },
                },
                "required": ["memory_type"],
            },
        ),
        types.Tool(
            name="traces_recent",
            description=(
                "Return the N most recent search traces — what memory nodes activated, "
                "in what order, for each search() call. Useful for diagnosing what Igor "
                "retrieved when processing a message."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of traces to return (default 10)",
                    },
                    "since_minutes": {
                        "type": "integer",
                        "description": "Only traces from last N minutes (optional)",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="tail_heat",
            description="Get current decaying activation heat for a node (sum of weighted recent activations).",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Memory node ID"},
                },
                "required": ["node_id"],
            },
        ),
        types.Tool(
            name="hot_nodes",
            description="List nodes with highest current tail heat — most recently and strongly activated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of nodes (default 10)",
                    },
                    "since_hours": {
                        "type": "number",
                        "description": "Only tails from last N hours (default 2)",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="turn_trace_recent",
            description=(
                "Read recent turn traces from Igor's reasoning log. "
                "Each entry shows: input preview, thalamus intent, BG top habit, "
                "habit fired (if any), tier used, cost, response preview. "
                "Essential for diagnosing why Igor responded a certain way."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of turns (default 5)",
                    },
                    "since_minutes": {
                        "type": "integer",
                        "description": "Only turns from last N minutes (optional)",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="cc_send",
            description=(
                "Inject a message into Igor's reasoning pipeline via the CC bridge. "
                "Igor will process it as a 'claude-code' author message — full BG scoring, "
                "habit matching, LLM response. Use for reading POC tests and diagnostics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Message to send to Igor",
                    },
                },
                "required": ["content"],
            },
        ),
        types.Tool(
            name="wg_neighbors",
            description="Get word graph neighbors for a node — edges and weights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "Word to look up"},
                    "limit": {
                        "type": "integer",
                        "description": "Max neighbors (default 20)",
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum edge score (default 0.1)",
                    },
                },
                "required": ["word"],
            },
        ),
        types.Tool(
            name="habit_list",
            description="List active habits — id, trigger, type, score metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Filter by id or trigger text (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 30)",
                    },
                },
                "required": [],
            },
        ),
    ]


# ── Tool implementations ───────────────────────────────────────────────────────


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = _dispatch(name, arguments)
    except Exception as e:
        result = f"ERROR: {e}"
    return [types.TextContent(type="text", text=str(result))]


def _dispatch(name: str, args: dict) -> str:
    if name == "memory_search":
        return _memory_search(
            args.get("query", ""), args.get("limit", 10), args.get("memory_type")
        )
    elif name == "memory_get":
        return _memory_get(args["memory_id"])
    elif name == "memory_list_by_type":
        return _memory_list_by_type(args["memory_type"], args.get("limit", 20))
    elif name == "traces_recent":
        return _traces_recent(args.get("limit", 10), args.get("since_minutes"))
    elif name == "tail_heat":
        return _tail_heat(args["node_id"])
    elif name == "hot_nodes":
        return _hot_nodes(args.get("limit", 10), args.get("since_hours", 2))
    elif name == "turn_trace_recent":
        return _turn_trace_recent(args.get("limit", 5), args.get("since_minutes"))
    elif name == "cc_send":
        return _cc_send(args["content"])
    elif name == "wg_neighbors":
        return _wg_neighbors(
            args["word"], args.get("limit", 20), args.get("min_score", 0.1)
        )
    elif name == "habit_list":
        return _habit_list(args.get("query"), args.get("limit", 30))
    else:
        return f"Unknown tool: {name}"


# ── memory_search ──────────────────────────────────────────────────────────────


def _memory_search(query: str, limit: int, memory_type: str | None) -> str:
    terms = query.lower().split()
    if not terms:
        return "No query terms provided."
    conditions = " OR ".join(["LOWER(narrative) LIKE %s"] * len(terms))
    params = [f"%{t}%" for t in terms]
    type_clause = ""
    if memory_type:
        type_clause = f" AND memory_type = %s"
        params.append(memory_type.upper())
    params.append(limit)
    rows = _q(
        f"SELECT id, memory_type, narrative, activation_count, metadata "
        f"FROM memories WHERE ({conditions}){type_clause} "
        f"ORDER BY activation_count DESC LIMIT %s",
        params,
    )
    if not rows:
        return f"No memories found for: {query}"
    lines = [f"Found {len(rows)} memories for '{query}':\n"]
    for r in rows:
        snippet = (r["narrative"] or "")[:120].replace("\n", " ")
        lines.append(f"  [{r['memory_type']}] {r['id']}\n    {snippet}")
    return "\n".join(lines)


# ── memory_get ────────────────────────────────────────────────────────────────


def _memory_get(memory_id: str) -> str:
    rows = _q(
        "SELECT id, memory_type, narrative, activation_count, metadata, "
        "parent_id, children_ids, link_ids, timestamp, last_accessed "
        "FROM memories WHERE id = %s",
        (memory_id,),
    )
    if not rows:
        return f"Memory not found: {memory_id}"
    r = rows[0]
    meta = r.get("metadata") or {}
    return (
        f"ID: {r['id']}\n"
        f"Type: {r['memory_type']}\n"
        f"Activations: {r['activation_count']}\n"
        f"Last accessed: {r['last_accessed']}\n"
        f"Parent: {r['parent_id']}\n"
        f"Children: {r['children_ids']}\n"
        f"Links: {r['link_ids']}\n"
        f"Metadata: {json.dumps(meta, indent=2)}\n"
        f"Narrative:\n{r['narrative']}"
    )


# ── memory_list_by_type ───────────────────────────────────────────────────────


def _memory_list_by_type(memory_type: str, limit: int) -> str:
    rows = _q(
        "SELECT id, narrative, activation_count FROM memories "
        "WHERE memory_type = %s ORDER BY activation_count DESC LIMIT %s",
        (memory_type.upper(), limit),
    )
    if not rows:
        return f"No memories of type {memory_type}"
    lines = [f"{len(rows)} {memory_type} memories:\n"]
    for r in rows:
        snippet = (r["narrative"] or "")[:100].replace("\n", " ")
        lines.append(f"  [{r['activation_count']}] {r['id']}\n    {snippet}")
    return "\n".join(lines)


# ── traces_recent ─────────────────────────────────────────────────────────────


def _traces_recent(limit: int, since_minutes: int | None) -> str:
    params = []
    where = ""
    if since_minutes:
        cutoff = (datetime.now() - timedelta(minutes=since_minutes)).isoformat()
        where = "WHERE recorded_at > %s "
        params.append(cutoff)
    params.append(limit)
    rows = _q(
        f"SELECT id, recorded_at, query, nodes FROM traces {where}"
        f"ORDER BY recorded_at DESC LIMIT %s",
        params,
    )
    if not rows:
        return "No traces found."
    lines = [f"{len(rows)} recent traces:\n"]
    for r in rows:
        nodes = json.loads(r["nodes"]) if isinstance(r["nodes"], str) else r["nodes"]
        type_counts: dict[str, int] = {}
        for n in nodes:
            t = n.get("memory_type", "?")
            type_counts[t] = type_counts.get(t, 0) + 1
        top3 = [f"{n['node_id']}({n['relevance']:.2f})" for n in nodes[:3]]
        lines.append(
            f"  {r['recorded_at'][:19]}  q={repr((r['query'] or '')[:50])}\n"
            f"    nodes={len(nodes)} types={type_counts}\n"
            f"    top3: {', '.join(top3)}"
        )
    return "\n".join(lines)


# ── tail_heat ─────────────────────────────────────────────────────────────────


def _tail_heat(node_id: str) -> str:
    rows = _q(
        "SELECT weight, recorded_at FROM tails WHERE node_id = %s "
        "ORDER BY recorded_at DESC LIMIT 50",
        (node_id,),
    )
    if not rows:
        return f"No tail entries for {node_id} — never activated or too old."
    # TAIL_GRADIENT: half_life = 24h = 0.5^(elapsed_hours/24)
    now = datetime.now()
    total = 0.0
    for r in rows:
        try:
            recorded_at = datetime.fromisoformat(str(r["recorded_at"]))
            elapsed_hours = (now - recorded_at).total_seconds() / 3600.0
            factor = 0.5 ** (max(0.0, elapsed_hours) / 24.0)
            total += (r["weight"] or 1.0) * factor
        except Exception:
            continue
    return f"Tail heat for {node_id}: {total:.4f} ({len(rows)} entries)"


# ── hot_nodes ─────────────────────────────────────────────────────────────────


def _hot_nodes(limit: int, since_hours: float) -> str:
    cutoff = (datetime.now() - timedelta(hours=since_hours)).isoformat()
    rows = _q(
        "SELECT node_id, SUM(weight) as raw_weight, MAX(recorded_at) as last_seen, COUNT(*) as hits "
        "FROM tails WHERE recorded_at > %s "
        "GROUP BY node_id ORDER BY raw_weight DESC LIMIT %s",
        (cutoff, limit * 3),  # fetch extra, will re-sort by decayed heat
    )
    if not rows:
        return f"No tail activity in last {since_hours}h."
    now = datetime.now()
    scored = []
    for r in rows:
        try:
            last = datetime.fromisoformat(str(r["last_seen"]))
            elapsed = (now - last).total_seconds() / 3600.0
            heat = float(r["raw_weight"] or 0) * (0.5 ** (elapsed / 24.0))
            scored.append((heat, r))
        except Exception:
            continue
    scored.sort(key=lambda x: -x[0])
    lines = [f"Hot nodes (last {since_hours}h):\n"]
    for heat, r in scored[:limit]:
        lines.append(
            f"  heat={heat:.3f} hits={r['hits']} id={r['node_id']} last={str(r['last_seen'])[:19]}"
        )
    return "\n".join(lines)


# ── turn_trace_recent ─────────────────────────────────────────────────────────


def _turn_trace_recent(limit: int, since_minutes: int | None) -> str:
    """Parse the turn_trace JSONL log — today's file."""
    # Find the right log file (today's date)
    log_dir = Path.home() / ".TheIgors" / "logs"
    today = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"turn_trace.{today[:4]}-{today[4:6]}-{today[6:]}.log"
    if not log_file.exists():
        # Try numeric format
        log_file = log_dir / f"turn_trace.{today}.log"
    if not log_file.exists():
        # Fallback: most recent turn_trace file
        files = sorted(
            log_dir.glob("turn_trace.*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if not files:
            return "No turn_trace log found."
        log_file = files[0]

    cutoff = None
    if since_minutes:
        cutoff = datetime.now() - timedelta(minutes=since_minutes)

    # Parse turn blocks — each is === turn ... === ... === END ===
    text = log_file.read_text(errors="replace")
    blocks = re.split(r"=== turn ", text)[1:]  # split on turn headers

    turns = []
    for block in blocks:
        try:
            header_end = block.index("\n")
            header = block[
                :header_end
            ]  # "52b3739f | web:shared | 2026-03-19T19:16:59 | 26170ms total"
            parts = [p.strip() for p in header.split("|")]
            turn_id = parts[0]
            ts_str = parts[2] if len(parts) > 2 else ""

            if cutoff:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < cutoff:
                        continue
                except Exception:
                    pass

            json_start = block.index("{")
            json_end = block.rindex("}") + 1
            data = json.loads(block[json_start:json_end])

            turns.append((ts_str, turn_id, data))
        except Exception:
            continue

    if not turns:
        return "No turns found in log."

    # Newest first
    turns.sort(key=lambda x: x[0], reverse=True)
    turns = turns[:limit]

    lines = [f"{len(turns)} recent turns:\n"]
    for ts, turn_id, d in turns:
        intent = d.get("thalamus", {}).get("intent", "?")
        bg = d.get("bg_prospect", {}).get("habit", "none")
        habit_fired = d.get("habit_exec", {}).get("habit_id", "—")
        tier = d.get("response", {}).get("tier", "?")
        cost = d.get("response", {}).get("cost_usd", 0)
        preview = (d.get("response", {}).get("preview") or "")[:80].replace("\n", " ")
        inp = (d.get("input") or "")[:60].replace("\n", " ")
        lines.append(
            f"  [{ts[:19]}] {turn_id}\n"
            f"    in:     {inp!r}\n"
            f"    intent: {intent}  BG: {bg}  fired: {habit_fired}  tier: {tier}  ${cost:.4f}\n"
            f"    out:    {preview!r}"
        )
    return "\n".join(lines)


# ── cc_send ───────────────────────────────────────────────────────────────────


def _cc_send(content: str) -> str:
    payload = json.dumps({"content": content}).encode()
    req = urllib.request.Request(
        CC_SEND_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    import ssl

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            resp = json.loads(r.read())
            return f"Sent. Igor response: {resp}"
    except Exception as e:
        return f"cc_send failed: {e}"


# ── wg_neighbors ──────────────────────────────────────────────────────────────


def _wg_neighbors(word: str, limit: int, min_score: float) -> str:
    rows = _q(
        "SELECT word_b as neighbor, score FROM wg_edges "
        "WHERE word_a = %s AND score >= %s "
        "ORDER BY score DESC LIMIT %s",
        (word.lower(), min_score, limit),
    )
    if not rows:
        # Try reverse
        rows = _q(
            "SELECT word_a as neighbor, score FROM wg_edges "
            "WHERE word_b = %s AND score >= %s "
            "ORDER BY score DESC LIMIT %s",
            (word.lower(), min_score, limit),
        )
    if not rows:
        return f"No wg_edges neighbors found for '{word}'"
    lines = [f"Neighbors of '{word}' ({len(rows)}):\n"]
    for r in rows:
        lines.append(f"  {r['score']:.4f}  {r['neighbor']}")
    return "\n".join(lines)


# ── habit_list ────────────────────────────────────────────────────────────────


def _habit_list(query: str | None, limit: int) -> str:
    params = []
    where = "WHERE metadata->>'trigger' IS NOT NULL "
    if query:
        where += "AND (LOWER(id) LIKE %s OR LOWER(metadata->>'trigger') LIKE %s) "
        params += [f"%{query.lower()}%", f"%{query.lower()}%"]
    params.append(limit)
    rows = _q(
        f"SELECT id, memory_type, metadata->>'trigger' as trigger, "
        f"metadata->>'habit_type' as habit_type "
        f"FROM memories {where}ORDER BY id LIMIT %s",
        params,
    )
    if not rows:
        return "No habits found."
    lines = [f"{len(rows)} habits:\n"]
    for r in rows:
        lines.append(
            f"  {r['id']}\n"
            f"    type={r['habit_type']}  trigger={repr((r['trigger'] or '')[:80])}"
        )
    return "\n".join(lines)


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
