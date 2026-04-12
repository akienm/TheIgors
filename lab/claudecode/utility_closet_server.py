#!/usr/bin/env python3
"""
Utility Closet Server — D335: shared agent platform layer.

Standalone Starlette/uvicorn server that runs independently of any agent.
Agents (Igor, future copilot, etc.) register as clients and push data.
Claude Code, web browsers, and other tools connect as consumers.

Endpoints (platform — always available):
  GET  /                      → serve web UI (fallback HTML if not built)
  GET  /assets/{path}         → serve web_ui/dist/assets/
  WS   /ws                    → WebSocket hub (chat, dashboard, activity)
  POST /api/cc_send           → inject message into channel (author: "claude-code")
  POST /api/upload            → save file to inbox
  GET  /api/outbox            → list outbox files
  GET  /api/outbox/{file}     → download from outbox
  GET  /api/sessions          → list active WebSocket sessions
  GET  /health                → platform health + PID + attached agents
  GET  /metrics               → platform metrics

Endpoints (agent — available when agent is registered):
  POST /api/agents/register   → agent announces itself
  POST /api/agents/deregister → agent disconnects
  POST /api/agents/{id}/stats → agent pushes dashboard data
  GET  /api/dashboard         → returns last-pushed stats from attached agent
  *    /api/agent/{id}/*      → proxied to agent's callback URL (future)

Lifecycle:
  - PID file at ~/.TheIgors/utility_closet.pid
  - /health responds within 5s or considered stalled
  - Launchers (superclaude, igor) start this if not running
  - Second instance detects running/stalled via PID + health check

Port: IGOR_UC_PORT env var, default 8080.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

# ── Logging ──────────────────────────────────────────────────────────────────

_LOG_DIR = Path(os.environ.get("IGOR_RUNTIME_ROOT", Path.home() / ".TheIgors")) / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_log_file = _LOG_DIR / "utility_closet.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(_log_file)),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("utility_closet")

# ── Paths ────────────────────────────────────────────────────────────────────

_RUNTIME_ROOT = Path(os.environ.get("IGOR_RUNTIME_ROOT", Path.home() / ".TheIgors"))
_INSTANCE_DIR = _RUNTIME_ROOT / os.environ.get("IGOR_INSTANCE_ID", "Igor-wild-0001")
_REPO_DIR = Path(__file__).parent.parent  # ~/TheIgors
_DIST_DIR = _REPO_DIR / "wild_igor" / "web_ui" / "dist"

INBOX_DIR = _INSTANCE_DIR / "inbox"
OUTBOX_DIR = _INSTANCE_DIR / "outbox"
PID_FILE = _RUNTIME_ROOT / "utility_closet.pid"

_CHANNEL_DIR = _RUNTIME_ROOT / "local" / "cc_channel"
_CHANNEL_FILE = _CHANNEL_DIR / "messages.jsonl"

# ── Boot timestamp ───────────────────────────────────────────────────────────

_boot_ts: float = time.monotonic()
_boot_wall: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
_last_input_ts: float = 0.0

# ── Agent registry ───────────────────────────────────────────────────────────
# Agents register on boot, deregister on shutdown. Thread-safe via lock.

_agents: dict = (
    {}
)  # agent_id → {registered_at, capabilities, last_stats, last_heartbeat}
_agents_lock = threading.Lock()
_agent_stats: dict = {}  # agent_id → last stats dict pushed by agent

# ── WebSocket session management ─────────────────────────────────────────────

_session_clients: dict = {}  # session_id → [asyncio.Queue, ...]
_client_session: dict = {}  # id(ws) → session_id
_session_history: dict = {}  # session_id → [{...}, ...] (capped at 50)
_client_lock = threading.Lock()
_loop: Optional[asyncio.AbstractEventLoop] = None

# ── Thread-safe queue: web messages → attached agent ─────────────────────────
import queue

incoming: queue.Queue = queue.Queue()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ensure_dirs():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    _CHANNEL_DIR.mkdir(parents=True, exist_ok=True)


def _bootstrap_mkcert() -> tuple[str, str] | None:
    """Generate a locally-trusted cert via mkcert if available.

    Returns (cert_path, key_path) on success, None if mkcert isn't installed
    or generation failed. Idempotent — reuses existing files.
    """
    import shutil
    import subprocess
    from pathlib import Path

    cert_dir = Path.home() / ".TheIgors" / "certs"
    cert_path = cert_dir / "localhost+3.pem"
    key_path = cert_dir / "localhost+3-key.pem"

    if cert_path.exists() and key_path.exists():
        return (str(cert_path), str(key_path))

    if not shutil.which("mkcert"):
        return None

    cert_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "mkcert",
                "-cert-file",
                str(cert_path),
                "-key-file",
                str(key_path),
                "localhost",
                "127.0.0.1",
                "::1",
            ],
            cwd=str(cert_dir),
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as e:
        log.warning("mkcert generation failed: %s", e)
        return None

    return (str(cert_path), str(key_path))


def _channel_append(author: str, content: str, msg_type: str = "message"):
    """Mirror a message to the shared JSONL channel and Postgres. Never raises."""
    try:
        _CHANNEL_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {"ts": ts, "author": author, "type": msg_type, "content": content}
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with open(_CHANNEL_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        # Mirror to Postgres channel_messages so MCP channel_read sees messages
        _pg_url = os.environ.get("IGOR_HOME_DB_URL", "") or os.environ.get(
            "IGOR_DB_URL", ""
        )
        if _pg_url:
            try:
                import psycopg2

                conn = psycopg2.connect(_pg_url)
                with conn:
                    with conn.cursor() as c:
                        c.execute(
                            "INSERT INTO channel_messages (ts, author, type, content) "
                            "VALUES (%s, %s, %s, %s)",
                            (ts, author, msg_type, content),
                        )
                conn.close()
            except Exception as pg_e:
                log.debug("channel_append PG write failed (non-fatal): %s", pg_e)
    except Exception as e:
        log.warning("channel_append error: %s", e)


def _add_to_history(session_id: str, msg: dict):
    """Add a message to session history (capped at 50)."""
    with _client_lock:
        hist = _session_history.setdefault(session_id, [])
        hist.append(msg)
        if len(hist) > 50:
            hist.pop(0)


def _broadcast_to_session(session_id: str, payload: str):
    """Fan out a payload to clients in a specific session."""
    if _loop is None:
        return
    with _client_lock:
        queues = list(_session_clients.get(session_id, []))
    for q in queues:
        _loop.call_soon_threadsafe(q.put_nowait, payload)


def _broadcast(payload: str):
    """Fan out a JSON payload to every connected WebSocket client (all sessions)."""
    if _loop is None:
        return
    with _client_lock:
        all_queues = [q for qs in _session_clients.values() for q in qs]
    for q in all_queues:
        _loop.call_soon_threadsafe(q.put_nowait, payload)


# ── Public send API (called by agents via REST) ─────────────────────────────


def agent_send(text: str, agent_id: str, session_id: str = "shared"):
    """An agent sends a response to the web UI."""
    msg = {
        "type": "message",
        "author": agent_id,
        "content": text,
        "ts": _ts(),
        "session_id": session_id,
    }
    _add_to_history(session_id, msg)
    _broadcast_to_session(session_id, json.dumps(msg))
    _channel_append(agent_id, text)


# ── Route handlers ───────────────────────────────────────────────────────────


async def _index(request: Request):
    index_file = _DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse(
        _FALLBACK_HTML,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


async def _api_upload(request: Request):
    _ensure_dirs()
    form = await request.form()
    file = form.get("file")
    if file is None:
        return JSONResponse({"error": "no file"}, status_code=400)
    safe_name = Path(file.filename).name
    dest = INBOX_DIR / safe_name
    content = await file.read()
    dest.write_bytes(content)
    incoming.put(
        {
            "content": f"[File uploaded: {safe_name}]",
            "filename": safe_name,
            "author": "web-user",
        }
    )
    _broadcast(json.dumps({"type": "file_dropped", "filename": safe_name, "ts": _ts()}))
    return JSONResponse({"status": "ok", "filename": safe_name})


async def _api_outbox_list(request: Request):
    _ensure_dirs()
    files = []
    try:
        for p in sorted(OUTBOX_DIR.iterdir()):
            if p.is_file():
                st = p.stat()
                files.append({"name": p.name, "size": st.st_size, "mtime": st.st_mtime})
    except OSError as e:
        log.warning("outbox list error: %s", e)
    return JSONResponse(files)


async def _api_outbox_download(request: Request):
    safe = Path(request.path_params["filename"]).name
    path = OUTBOX_DIR / safe
    if not path.exists():
        return Response("Not found", status_code=404)
    return FileResponse(str(path), filename=safe)


async def _api_cc_send(request: Request):
    """CC->channel: Claude Code injects a message with author 'claude-code'."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    content = body.get("content", "").strip()
    if not content:
        return JSONResponse({"error": "empty content"}, status_code=400)
    global _last_input_ts
    _last_input_ts = time.monotonic()
    incoming.put({"content": content, "author": "claude-code"})
    _broadcast(
        json.dumps(
            {
                "type": "message",
                "author": "claude-code",
                "content": content,
                "ts": _ts(),
            }
        )
    )
    _channel_append("claude-code", content)
    return JSONResponse({"status": "ok"})


async def _api_health(request: Request):
    """GET /health — platform liveness probe."""
    now = time.monotonic()
    uptime_s = round(now - _boot_ts, 1)
    last_input_ago_s = round(now - _last_input_ts, 1) if _last_input_ts > 0 else None
    with _agents_lock:
        agents = list(_agents.keys())
    with _client_lock:
        ws_clients = sum(len(qs) for qs in _session_clients.values())
    return JSONResponse(
        {
            "status": "ok",
            "uptime_s": uptime_s,
            "boot_ts": _boot_wall,
            "last_input_ago_s": last_input_ago_s,
            "active_threads": threading.active_count(),
            "ws_clients": ws_clients,
            "attached_agents": agents,
            "pid": os.getpid(),
            "ts": _ts(),
        }
    )


def _swap_pct() -> float | None:
    """Read swap usage % from /proc/meminfo. Returns None if unavailable."""
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 2:
                    info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("SwapTotal", 0)
        if total == 0:
            return 0.0
        free = info.get("SwapFree", 0)
        return round((total - free) / total * 100, 1)
    except Exception:
        return None


async def _api_metrics(request: Request):
    """GET /metrics — platform metrics snapshot."""
    now = time.monotonic()
    payload = {
        "uptime_s": round(now - _boot_ts, 1),
        "active_threads": threading.active_count(),
        "swap_pct": _swap_pct(),
        "ts": _ts(),
    }
    # Include last-pushed agent stats if any
    with _agents_lock:
        for agent_id, stats in _agent_stats.items():
            payload[f"agent_{agent_id}"] = stats
    return JSONResponse(payload)


async def _api_dashboard(request: Request):
    """GET /api/dashboard — returns last stats pushed by the primary attached agent."""
    with _agents_lock:
        # Return first agent's stats (typically Igor)
        for agent_id, stats in _agent_stats.items():
            data = dict(stats)
            data["ts"] = _ts()
            data["agent"] = agent_id
            return JSONResponse(data)
    return JSONResponse({"ts": _ts(), "status": "no agent attached"})


async def _api_sessions(request: Request):
    """GET /api/sessions — list active sessions and their client counts."""
    with _client_lock:
        sessions = {sid: len(qs) for sid, qs in _session_clients.items() if qs}
    return JSONResponse({"sessions": sessions})


# ── HTML dashboard + metrics pages ────────────────────────────────────────────

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard — Agentic Utility Closet</title>
<style>
  body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
  h1 { color: #7ec8e3; margin-bottom: 1rem; font-size: 1.2rem; }
  .card { background: #2a2a3e; border: 1px solid #444; padding: 1rem; margin: 0.5rem 0;
          border-radius: 4px; }
  .card h2 { color: #90ee90; font-size: 1rem; margin-bottom: 0.5rem; }
  .stat { display: inline-block; margin-right: 1.5rem; }
  .stat .label { color: #888; font-size: 0.85rem; }
  .stat .value { color: #e0e0e0; font-size: 1.1rem; font-weight: bold; }
  .agent { border-left: 3px solid #4caf50; padding-left: 0.8rem; margin: 0.5rem 0; }
  .agent.none { border-color: #555; color: #888; }
  a { color: #7ec8e3; }
  #data { white-space: pre-wrap; }
</style></head><body>
<h1>Agentic Utility Closet — Dashboard</h1>
<div id="platform" class="card"><h2>Platform</h2><div id="plat-stats">loading...</div></div>
<div id="agents" class="card"><h2>Attached Agents</h2><div id="agent-list">loading...</div></div>
<div id="agent-data" class="card"><h2>Agent Data</h2><div id="data">loading...</div></div>
<p style="margin-top:1rem;font-size:0.8rem;color:#555"><a href="/">Chat</a> | <a href="/dashboard">Dashboard</a> | <a href="/metrics">Metrics</a></p>
<script>
async function refresh() {
  try {
    const h = await (await fetch('/health')).json();
    document.getElementById('plat-stats').innerHTML =
      '<span class="stat"><span class="label">uptime</span> <span class="value">' + Math.round(h.uptime_s) + 's</span></span>' +
      '<span class="stat"><span class="label">ws clients</span> <span class="value">' + h.ws_clients + '</span></span>' +
      '<span class="stat"><span class="label">threads</span> <span class="value">' + h.active_threads + '</span></span>' +
      '<span class="stat"><span class="label">pid</span> <span class="value">' + h.pid + '</span></span>';
    const aa = h.attached_agents || [];
    document.getElementById('agent-list').innerHTML = aa.length
      ? aa.map(a => '<div class="agent">' + a + '</div>').join('')
      : '<div class="agent none">No agents attached</div>';
  } catch(e) { document.getElementById('plat-stats').textContent = 'Error: ' + e; }
  try {
    const d = await (await fetch('/api/dashboard')).json();
    document.getElementById('data').textContent = JSON.stringify(d, null, 2);
  } catch(e) {}
}
refresh(); setInterval(refresh, 3000);
</script></body></html>"""


_METRICS_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Metrics — Agentic Utility Closet</title>
<style>
  body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
  h1 { color: #7ec8e3; margin-bottom: 1rem; font-size: 1.2rem; }
  pre { background: #2a2a3e; border: 1px solid #444; padding: 1rem; border-radius: 4px;
        overflow-x: auto; font-size: 0.9rem; }
  a { color: #7ec8e3; }
</style></head><body>
<h1>Agentic Utility Closet — Metrics</h1>
<pre id="data">loading...</pre>
<p style="margin-top:1rem;font-size:0.8rem;color:#555"><a href="/">Chat</a> | <a href="/dashboard">Dashboard</a> | <a href="/metrics">Metrics</a></p>
<script>
async function refresh() {
  try {
    const m = await (await fetch('/api/metrics')).json();
    document.getElementById('data').textContent = JSON.stringify(m, null, 2);
  } catch(e) { document.getElementById('data').textContent = 'Error: ' + e; }
}
refresh(); setInterval(refresh, 5000);
</script></body></html>"""


async def _page_dashboard(request: Request):
    """GET /dashboard — HTML dashboard page."""
    return HTMLResponse(_DASHBOARD_HTML)


async def _page_metrics(request: Request):
    """GET /metrics-page — HTML metrics page (distinct from JSON /metrics)."""
    return HTMLResponse(_METRICS_HTML)


# ── Agent registration ───────────────────────────────────────────────────────


async def _api_agent_register(request: Request):
    """POST /api/agents/register — agent announces itself."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    agent_id = body.get("agent_id", "").strip()
    if not agent_id:
        return JSONResponse({"error": "agent_id required"}, status_code=400)
    capabilities = body.get("capabilities", [])
    callback_url = body.get("callback_url", "")
    with _agents_lock:
        _agents[agent_id] = {
            "registered_at": _ts(),
            "capabilities": capabilities,
            "callback_url": callback_url,
            "last_heartbeat": time.monotonic(),
        }
    log.info("Agent registered: %s (capabilities: %s)", agent_id, capabilities)
    _broadcast(
        json.dumps(
            {
                "type": "agent_status",
                "agent_id": agent_id,
                "status": "attached",
                "ts": _ts(),
            }
        )
    )
    return JSONResponse({"status": "ok", "agent_id": agent_id})


async def _api_agent_deregister(request: Request):
    """POST /api/agents/deregister — agent disconnects."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    agent_id = body.get("agent_id", "").strip()
    with _agents_lock:
        _agents.pop(agent_id, None)
        _agent_stats.pop(agent_id, None)
    log.info("Agent deregistered: %s", agent_id)
    _broadcast(
        json.dumps(
            {
                "type": "agent_status",
                "agent_id": agent_id,
                "status": "detached",
                "ts": _ts(),
            }
        )
    )
    return JSONResponse({"status": "ok"})


async def _api_agent_stats(request: Request):
    """POST /api/agents/{id}/stats — agent pushes dashboard data."""
    agent_id = request.path_params.get("agent_id", "")
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    with _agents_lock:
        if agent_id not in _agents:
            return JSONResponse({"error": "agent not registered"}, status_code=404)
        _agents[agent_id]["last_heartbeat"] = time.monotonic()
        _agent_stats[agent_id] = body
    # Broadcast dashboard update to all WS clients
    _broadcast(
        json.dumps({"type": "dashboard", "agent": agent_id, **body, "ts": _ts()})
    )
    return JSONResponse({"status": "ok"})


async def _api_agent_send(request: Request):
    """POST /api/agents/{id}/send — agent sends a message to web UI."""
    agent_id = request.path_params.get("agent_id", "")
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    content = body.get("content", "").strip()
    session_id = body.get("session_id", "shared")
    if not content:
        return JSONResponse({"error": "empty content"}, status_code=400)
    agent_send(content, agent_id, session_id)
    return JSONResponse({"status": "ok"})


async def _api_agent_poll(request: Request):
    """GET /api/agents/{id}/poll — agent polls for incoming messages.

    Returns messages from the incoming queue addressed to this agent.
    Non-blocking: returns empty list if no messages.
    """
    messages = []
    try:
        while not incoming.empty():
            msg = incoming.get_nowait()
            messages.append(msg)
    except Exception as e:
        log.debug("incoming queue drain error (non-fatal): %s", e)
    return JSONResponse({"messages": messages})


# ── WebSocket endpoint ───────────────────────────────────────────────────────


async def _ws_endpoint(ws: WebSocket):
    await ws.accept()
    q: asyncio.Queue = asyncio.Queue()
    current_session = "shared"
    with _client_lock:
        _session_clients.setdefault(current_session, []).append(q)
        _client_session[id(ws)] = current_session

    # Send session history to newly joined client
    with _client_lock:
        hist = list(_session_history.get(current_session, []))
    if hist:
        await ws.send_text(
            json.dumps(
                {
                    "type": "session_history",
                    "session_id": current_session,
                    "messages": hist,
                }
            )
        )

    # Send agent status
    with _agents_lock:
        agents = list(_agents.keys())
    await ws.send_text(
        json.dumps(
            {
                "type": "platform_status",
                "attached_agents": agents,
                "ts": _ts(),
            }
        )
    )

    async def _receive():
        nonlocal current_session
        try:
            while True:
                data = await ws.receive_text()
                try:
                    msg = json.loads(data)
                except json.JSONDecodeError:
                    continue
                mtype = msg.get("type")

                if mtype == "identify":
                    _iname = (msg.get("name") or "").strip()[:60]
                    if _iname:
                        incoming.put(
                            {
                                "content": f"__identify__:{_iname}",
                                "author": _iname,
                                "client_id": id(ws),
                                "session_id": current_session,
                            }
                        )

                elif mtype == "join_session":
                    new_sid = (msg.get("session_id") or "shared").strip()[
                        :64
                    ] or "shared"
                    with _client_lock:
                        old_qs = _session_clients.get(current_session, [])
                        if q in old_qs:
                            old_qs.remove(q)
                        _session_clients.setdefault(new_sid, []).append(q)
                        _client_session[id(ws)] = new_sid
                        hist = list(_session_history.get(new_sid, []))
                    current_session = new_sid
                    await ws.send_text(
                        json.dumps(
                            {
                                "type": "session_history",
                                "session_id": new_sid,
                                "messages": hist,
                            }
                        )
                    )

                elif mtype == "message":
                    content = msg.get("content", "").strip()
                    author = msg.get("author", "web-user")
                    if content:
                        global _last_input_ts
                        _last_input_ts = time.monotonic()
                        incoming.put(
                            {
                                "content": content,
                                "author": author,
                                "client_id": id(ws),
                                "session_id": current_session,
                            }
                        )
                        umsg = {
                            "type": "message",
                            "author": author,
                            "content": content,
                            "ts": _ts(),
                            "session_id": current_session,
                        }
                        _add_to_history(current_session, umsg)
                        _broadcast_to_session(current_session, json.dumps(umsg))
                        _channel_append(author, content)
        except Exception as e:
            log.debug("ws receive error: %s", e)

    async def _forward():
        try:
            while True:
                payload = await q.get()
                await ws.send_text(payload)
        except Exception as e:
            log.debug("ws forward error: %s", e)

    recv = asyncio.ensure_future(_receive())
    fwd = asyncio.ensure_future(_forward())
    await asyncio.wait([recv, fwd], return_when=asyncio.FIRST_COMPLETED)
    for t in (recv, fwd):
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

    with _client_lock:
        qs = _session_clients.get(current_session, [])
        if q in qs:
            qs.remove(q)
        _client_session.pop(id(ws), None)


# ── Starlette app factory ───────────────────────────────────────────────────


def _make_app() -> Starlette:
    async def on_startup():
        global _loop
        _loop = asyncio.get_running_loop()

    routes = [
        Route("/", _index),
        WebSocketRoute("/ws", _ws_endpoint),
        # Platform endpoints
        Route("/api/upload", _api_upload, methods=["POST"]),
        Route("/api/cc_send", _api_cc_send, methods=["POST"]),
        Route("/api/outbox", _api_outbox_list),
        Route("/api/outbox/{filename}", _api_outbox_download),
        Route("/health", _api_health),
        Route("/api/health", _api_health),
        Route("/metrics", _api_metrics),
        Route("/api/metrics", _api_metrics),
        Route("/api/dashboard", _api_dashboard),
        Route("/api/sessions", _api_sessions),
        # HTML pages
        Route("/dashboard", _page_dashboard),
        Route("/metrics-page", _page_metrics),
        # Agent management
        Route("/api/agents/register", _api_agent_register, methods=["POST"]),
        Route("/api/agents/deregister", _api_agent_deregister, methods=["POST"]),
        Route("/api/agents/{agent_id}/stats", _api_agent_stats, methods=["POST"]),
        Route("/api/agents/{agent_id}/send", _api_agent_send, methods=["POST"]),
        Route("/api/agents/{agent_id}/poll", _api_agent_poll),
    ]

    # Serve compiled Svelte assets if the UI has been built
    assets_dir = _DIST_DIR / "assets"
    if assets_dir.exists():
        routes.append(
            Mount("/assets", app=StaticFiles(directory=str(assets_dir)), name="assets")
        )

    return Starlette(routes=routes, on_startup=[on_startup])


# ── PID file management ─────────────────────────────────────────────────────


def _write_pid():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    log.info("PID file written: %s (pid=%d)", PID_FILE, os.getpid())


def _remove_pid():
    try:
        if PID_FILE.exists():
            stored_pid = int(PID_FILE.read_text().strip())
            if stored_pid == os.getpid():
                PID_FILE.unlink()
                log.info("PID file removed")
    except Exception as e:
        log.warning("PID file cleanup error: %s", e)


def check_running() -> dict | None:
    """Check if another utility closet instance is running.

    Returns health dict if running and healthy, None otherwise.
    Kills stalled instances (PID exists but health check fails).
    """
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None

    # Check if process exists
    try:
        os.kill(pid, 0)
    except OSError:
        # Process doesn't exist — stale PID file
        log.info("Stale PID file (pid=%d not running), removing", pid)
        PID_FILE.unlink(missing_ok=True)
        return None

    # Process exists — check health
    # Try multiple URLs: SSL may be active (main port is HTTPS), and there
    # may be a plain HTTP fallback on a different port.
    port = int(os.environ.get("IGOR_UC_PORT", "8080"))
    http_port = int(os.environ.get("IGOR_UC_HTTP_PORT", "8082"))
    ssl_active = bool(os.environ.get("IGOR_SSL_CERT"))
    urls = []
    if ssl_active:
        urls.append(f"https://localhost:{port}/health")
    urls.append(f"http://localhost:{port}/health")
    if ssl_active:
        urls.append(f"http://localhost:{http_port}/health")
    import urllib.request
    import ssl as _ssl

    for url in urls:
        try:
            ctx = None
            if url.startswith("https://"):
                ctx = _ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = _ssl.CERT_NONE
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "ok":
                    return data
        except Exception as e:
            log.debug("health check %s failed (pid=%d): %s", url, pid, e)

    # Process exists but health check failed — stalled
    log.warning("Stalled utility closet (pid=%d), killing", pid)
    try:
        os.kill(pid, signal.SIGTERM)
        # Give it a moment to die
        import time as _time

        _time.sleep(1)
        try:
            os.kill(pid, 0)
            # Still alive — force kill
            os.kill(pid, signal.SIGKILL)
        except OSError:
            log.debug("process %d already dead during cleanup", pid)
    except OSError as e:
        log.warning("Failed to kill stalled process %d: %s", pid, e)
    PID_FILE.unlink(missing_ok=True)
    return None


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Utility Closet Server (D335)")
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("IGOR_UC_PORT", "8080"))
    )
    parser.add_argument(
        "--check", action="store_true", help="Check if running, exit 0 if healthy"
    )
    parser.add_argument("--stop", action="store_true", help="Stop running instance")
    args = parser.parse_args()

    if args.check:
        health = check_running()
        if health:
            print(json.dumps(health, indent=2))
            sys.exit(0)
        else:
            print("Not running")
            sys.exit(1)

    if args.stop:
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"Sent SIGTERM to {pid}")
                PID_FILE.unlink(missing_ok=True)
            except Exception as e:
                print(f"Stop failed: {e}")
                sys.exit(1)
        else:
            print("Not running (no PID file)")
        sys.exit(0)

    # Check for existing instance
    health = check_running()
    if health:
        log.info(
            "Utility closet already running (pid=%s, uptime=%ss)",
            health.get("pid"),
            health.get("uptime_s"),
        )
        sys.exit(0)

    # Start server
    _write_pid()
    _ensure_dirs()
    log.info("Utility closet starting on port %d", args.port)

    def _shutdown(signum, frame):
        log.info("Received signal %d, shutting down", signum)
        # Broadcast shutdown to all agents
        _broadcast(json.dumps({"type": "platform_shutdown", "ts": _ts()}))
        _remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    ssl_cert = os.environ.get("IGOR_SSL_CERT", "")
    ssl_key = os.environ.get("IGOR_SSL_KEY", "")

    # Bootstrap a locally-trusted cert via mkcert if none configured or files
    # are missing. Falls back to plain HTTP if mkcert isn't installed.
    if not (
        ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key)
    ):
        bootstrapped = _bootstrap_mkcert()
        if bootstrapped:
            ssl_cert, ssl_key = bootstrapped
            log.info("mkcert bootstrap: using %s", ssl_cert)
        else:
            log.warning(
                "No SSL cert configured and mkcert bootstrap unavailable — serving plain HTTP"
            )

    app = _make_app()
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=args.port,
        log_level="warning",
        ssl_certfile=ssl_cert if ssl_cert else None,
        ssl_keyfile=ssl_key if ssl_key else None,
    )
    server = uvicorn.Server(config)

    # When SSL is active, also serve plain HTTP on port+1 for LAN access
    # without cert warnings (same pattern as Igor's server.py)
    if ssl_cert and ssl_key:
        http_port = int(os.environ.get("IGOR_UC_HTTP_PORT", "8082"))
        log.info("SSL active — also serving plain HTTP on port %d", http_port)

        def _run_http():
            http_app = _make_app()
            http_config = uvicorn.Config(
                http_app,
                host="0.0.0.0",
                port=http_port,
                log_level="warning",
            )
            http_server = uvicorn.Server(http_config)
            asyncio.run(http_server.serve())

        import threading

        threading.Thread(target=_run_http, daemon=True, name="uc-http-fallback").start()

    try:
        asyncio.run(server.serve())
    finally:
        _remove_pid()


# ── Fallback HTML ────────────────────────────────────────────────────────────
# Copied from server.py — fully functional single-page chat UI.
# TODO: Phase 4 will update this to show agent attach/detach state.

_FALLBACK_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agentic Utility Closet</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: monospace; background: #1a1a2e; color: #e0e0e0;
           height: 100vh; display: flex; flex-direction: column; }
    #chat { flex: 1; overflow-y: auto; padding: 1rem;
            display: flex; flex-direction: column; gap: 0.4rem; }
    .msg { font-size: 0.95rem; line-height: 1.5; }
    .msg-user   .author { color: #7ec8e3; font-weight: bold; }
    .msg-igor   .author { color: #90ee90; font-weight: bold; }
    .msg-cc     .author { color: #ffb347; font-weight: bold; }
    .msg-system { color: #888; font-style: italic; }
    .author { margin-right: 0.4rem; }
    .content { white-space: pre-wrap; }
    .md p { margin: 0.3em 0; }
    .md p:first-child { margin-top: 0; }
    .md h1, .md h2, .md h3 { color: #90ee90; margin: 0.5em 0 0.2em; font-size: 1em; }
    .md strong { color: #e8e8f0; font-weight: bold; }
    .md em { font-style: italic; color: #c8c8d8; }
    .md ul, .md ol { margin: 0.3em 0 0.3em 1.4em; padding: 0; }
    .md li { margin: 0.1em 0; }
    .md code { background: #2a2a4a; padding: 0.1em 0.3em; border-radius: 2px;
               font-family: monospace; font-size: 0.9em; color: #aaddff; }
    .md pre { background: #2a2a4a; padding: 0.6em; margin: 0.4em 0;
              overflow-x: auto; border-left: 2px solid #4a4a8a; }
    .md pre code { background: none; padding: 0; color: #cce; }
    .md hr { border: none; border-top: 1px solid #333; margin: 0.5em 0; }
    .md blockquote { border-left: 2px solid #555; margin: 0.3em 0;
                     padding-left: 0.7em; color: #aaa; }
    #conn-led { font-size: 1.1em; line-height: 1; transition: color 0.3s; color: #555;
                cursor: default; }
    #conn-led.on  { color: #4caf50; }
    #conn-led.off { color: #f44336; }
    #agent-status { font-size: 0.75rem; color: #666; padding: 0 0.4rem; }
    #agent-status.attached { color: #4caf50; }
    #name-row { display: flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.5rem 0;
                border-top: 1px solid #333; font-size: 0.78rem; color: #888; }
    #sender-name { width: 7em; background: #1e1e30; color: #aaa; border: 1px solid #444;
                   padding: 0.2rem 0.4rem; font-family: monospace; font-size: 0.78rem; }
    #input-row { display: flex; gap: 0.5rem; padding: 0.3rem 0.5rem 0.5rem; }
    #input { flex: 1; background: #2a2a3e; color: #e0e0e0;
             border: 1px solid #555; padding: 0.5rem;
             font-family: monospace; font-size: 1rem;
             resize: vertical; min-height: 2.2em; max-height: 30vh;
             overflow-y: auto; }
    button { background: #4a4a8a; color: #fff; border: none;
             padding: 0.5rem 1rem; cursor: pointer; font-family: monospace; }
    button:hover { background: #6a6aaa; }
    #status-bar { padding: 0.2rem 1rem; background: #0a0a18;
                  font-size: 0.78rem; color: #aaa; border-top: 1px solid #1a1a30;
                  min-height: 1.4em; transition: color 0.3s; }
    #status-bar.busy { color: #7ec8e3; }
    #dashboard { padding: 0.3rem 1rem; background: #0f0f1e;
                 font-size: 0.8rem; color: #888; border-top: 1px solid #222;
                 display: flex; gap: 1rem; }
    #ring-feed { max-height: 0; overflow: hidden; transition: max-height 0.3s ease;
                 background: #080814; border-top: 1px solid #1a1a30; }
    #ring-feed.open { max-height: 14em; overflow-y: auto; }
    #ring-feed table { width: 100%; border-collapse: collapse; font-size: 0.73rem;
                       font-family: monospace; color: #99a; }
    #ring-feed td { padding: 0.15rem 0.5rem; border-bottom: 1px solid #111; vertical-align: top; }
    #ring-feed td.cat { color: #7ec8e3; white-space: nowrap; width: 12em; }
    #ring-toggle { cursor: pointer; user-select: none; padding: 0 0.4rem; color: #555;
                   font-size: 0.85em; }
    #ring-toggle:hover { color: #aaa; }
    #surprise-feed { max-height: 0; overflow: hidden; transition: max-height 0.3s ease;
                     background: #080814; border-top: 1px solid #1a1a30; }
    #surprise-feed.open { max-height: 10em; overflow-y: auto; }
    #surprise-feed table { width: 100%; border-collapse: collapse; font-size: 0.73rem;
                           font-family: monospace; color: #99a; }
    #surprise-feed td { padding: 0.15rem 0.5rem; border-bottom: 1px solid #111; vertical-align: top; }
    #surprise-toggle { cursor: pointer; user-select: none; padding: 0 0.4rem; color: #555;
                       font-size: 0.85em; }
    #surprise-toggle:hover { color: #aaa; }
    #surprise-avg.low  { color: #5c5; }
    #surprise-avg.mid  { color: #cc5; }
    #surprise-avg.high { color: #c55; }
    #drop-overlay { display: none; position: fixed; inset: 0; z-index: 100;
                    background: rgba(74,74,138,0.8); align-items: center;
                    justify-content: center; font-size: 2rem; color: #fff;
                    border: 4px dashed #7ec8e3; }
    #drop-overlay.active { display: flex; }
    #session-bar { display: flex; gap: 0; align-items: center; background: #0d0d22;
                   border-bottom: 1px solid #1a1a30; padding: 0.1rem 0.4rem; overflow-x: auto;
                   white-space: nowrap; flex-shrink: 0; }
    .session-tab { font-family: monospace; font-size: 0.78rem; padding: 0.2rem 0.6rem;
                   cursor: pointer; color: #888; border: 1px solid transparent;
                   border-radius: 2px 2px 0 0; background: transparent; transition: color 0.2s; }
    .session-tab:hover  { color: #ccc; }
    .session-tab.active { color: #7ec8e3; border-color: #1a1a30; background: #1a1a2e; }
    #new-session-btn { font-family: monospace; font-size: 0.82rem; padding: 0.1rem 0.5rem;
                       cursor: pointer; color: #555; background: transparent; border: none;
                       margin-left: 0.3rem; }
    #new-session-btn:hover { color: #aaa; }
    #content-area { flex: 1; display: flex; overflow: hidden; min-height: 0; }
    #bridge-pane { width: 42%; border-left: 1px solid #2a1a40; display: flex;
                   flex-direction: column; min-height: 0; background: #130d1e; }
    #bridge-header { padding: 0.25rem 0.6rem; background: #0a0717;
                     border-bottom: 1px solid #2a1a40; font-size: 0.75rem;
                     color: #c8a0ff; flex-shrink: 0; }
    #bridge-chat { flex: 1; overflow-y: auto; padding: 0.6rem;
                   display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.88rem; }
    .msg-claude .author { color: #c8a0ff; font-weight: bold; }
    #back-row { display: flex; gap: 0.4rem; padding: 0.3rem 0.4rem;
                border-top: 1px solid #2a1a40; flex-shrink: 0; }
    #back-input { flex: 1; background: #180d26; color: #e0e0e0; border: 1px solid #4a2a6a;
                  padding: 0.3rem 0.5rem; font-family: monospace; font-size: 0.85rem;
                  resize: none; min-height: 2em; }
    #cc-toggle { font-family: monospace; font-size: 0.78rem; color: #555;
                 background: transparent; border: 1px solid #444;
                 padding: 0.2rem 0.5rem; cursor: pointer; }
    #cc-toggle.active { color: #c8a0ff; border-color: #c8a0ff; }
  </style>
</head>
<body>
  <div id="drop-overlay">Drop file to send</div>
  <div id="session-bar">
    <span class="session-tab active" data-sid="shared" onclick="switchSession('shared')">shared</span>
    <button id="new-session-btn" onclick="newSession()" title="New session">+</button>
  </div>
  <div id="content-area">
    <div id="chat"></div>
    <div id="bridge-pane" style="display:none">
      <div id="bridge-header">Claude bridge  <span id="bridge-count" style="color:#555;float:right"></span></div>
      <div id="bridge-chat"></div>
      <div id="back-row">
        <textarea id="back-input" placeholder="Claude only (back channel)..." rows="2" autocomplete="off"></textarea>
        <button onclick="sendBack()">CC</button>
      </div>
    </div>
  </div>
  <div id="status-bar">idle</div>
  <div id="name-row">
    <span id="conn-led" title="Connection status">*</span>
    <span id="agent-status">no agent</span>
    <label for="sender-name">Your name:</label>
    <input id="sender-name" type="text" value="akien" maxlength="32" autocomplete="off">
    <button id="cc-toggle" onclick="toggleCC()" title="Toggle Claude bridge pane">CC</button>
    <button onclick="changeFontSize(-1)" title="Decrease font size" style="padding:0.2rem 0.5rem;font-size:0.85rem;">A-</button>
    <button onclick="changeFontSize(1)" title="Increase font size" style="padding:0.2rem 0.5rem;font-size:0.85rem;">A+</button>
  </div>
  <div id="input-row">
    <textarea id="input" placeholder="Message the channel..." autocomplete="off" rows="4"></textarea>
    <button onclick="sendMsg()">Send</button>
    <button onclick="document.getElementById('file-input').click()">clip</button>
    <input id="file-input" type="file" style="display:none" onchange="uploadFile(this)">
  </div>
  <div id="dashboard"><span>Connecting...</span><span id="ring-toggle" onclick="toggleRing()" title="Toggle ring feed">v ring</span><span id="surprise-toggle" onclick="toggleSurprise()" title="Toggle prediction surprise feed">v surprise</span></div>
  <div id="ring-feed"><table id="ring-table"><tr><td colspan="2">loading...</td></tr></table></div>
  <div id="surprise-feed"><table id="surprise-table"><tr><td>loading...</td></tr></table></div>
  <script>
    const chat       = document.getElementById('chat');
    const input      = document.getElementById('input');
    const senderName = document.getElementById('sender-name');
    const dash       = document.getElementById('dashboard');
    const status     = document.getElementById('status-bar');
    const overlay    = document.getElementById('drop-overlay');
    const agentStatus = document.getElementById('agent-status');
    const ringFeed      = document.getElementById('ring-feed');
    const ringTable     = document.getElementById('ring-table');
    const surpriseFeed  = document.getElementById('surprise-feed');
    const surpriseTable = document.getElementById('surprise-table');
    let ws, dragDepth = 0, ringOpen = false, surpriseOpen = false;
    const _knownAgents = new Set();  // populated by platform_status / agent_status
    const _urlSession = new URLSearchParams(location.search).get('session') || 'shared';
    let currentSession = _urlSession;
    const sessionMsgs = {'shared': []};
    if (_urlSession !== 'shared') sessionMsgs[_urlSession] = [];
    const sessionBar = document.getElementById('session-bar');

    function _saveName(n) {
      localStorage.setItem('igor_sender_name', n);
      document.cookie = 'igor_user=' + encodeURIComponent(n) + '; path=/; max-age=31536000; SameSite=Lax';
    }
    function _loadName() {
      const _ck = document.cookie.split(';').map(c => c.trim())
        .find(c => c.startsWith('igor_user='));
      if (_ck) return decodeURIComponent(_ck.split('=')[1]);
      return localStorage.getItem('igor_sender_name') || '';
    }
    const _savedName = _loadName();
    if (_savedName) senderName.value = _savedName;
    senderName.addEventListener('change', () => _saveName(senderName.value));

    let _fontSize = parseFloat(localStorage.getItem('igor_font_size') || '0.95');
    function _applyFontSize() { document.getElementById('chat').style.fontSize = _fontSize + 'rem'; }
    function changeFontSize(delta) {
      _fontSize = Math.min(Math.max(_fontSize + delta * 0.1, 0.6), 2.0);
      _fontSize = Math.round(_fontSize * 100) / 100;
      localStorage.setItem('igor_font_size', String(_fontSize));
      _applyFontSize();
    }
    _applyFontSize();

    function _renderSessionBar() {
      const existing = new Set([...sessionBar.querySelectorAll('.session-tab')].map(t => t.dataset.sid));
      Object.keys(sessionMsgs).forEach(sid => {
        if (!existing.has(sid)) {
          const tab = document.createElement('span');
          tab.className = 'session-tab'; tab.dataset.sid = sid; tab.textContent = sid;
          tab.onclick = () => switchSession(sid);
          sessionBar.insertBefore(tab, document.getElementById('new-session-btn'));
        }
      });
      sessionBar.querySelectorAll('.session-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.sid === currentSession);
      });
    }

    function _renderSession(sid) {
      chat.innerHTML = '';
      (sessionMsgs[sid] || []).forEach(m => {
        const cls = m.author === 'claude-code' ? 'cc' : _knownAgents.has(m.author) ? 'igor' : 'user';
        const label = m.author === 'claude-code' ? 'CC>' : (m.author || 'You');
        addMsg(cls, label, m.content);
      });
    }

    function switchSession(sid) {
      if (!sessionMsgs[sid]) sessionMsgs[sid] = [];
      currentSession = sid;
      history.replaceState({}, '', sid === 'shared' ? '/' : '/?session=' + encodeURIComponent(sid));
      _renderSessionBar(); _renderSession(sid);
      if (ws && ws.readyState === 1)
        ws.send(JSON.stringify({type: 'join_session', session_id: sid}));
    }

    function newSession() {
      const name = prompt('Session name (blank for random):');
      if (name === null) return;
      const sid = name.trim() || 'session-' + Date.now().toString(36);
      switchSession(sid);
    }

    function toggleRing() {
      ringOpen = !ringOpen;
      ringFeed.className = ringOpen ? 'open' : '';
      document.getElementById('ring-toggle').textContent = (ringOpen ? '^ ' : 'v ') + 'ring';
    }

    function toggleSurprise() {
      surpriseOpen = !surpriseOpen;
      surpriseFeed.className = surpriseOpen ? 'open' : '';
      document.getElementById('surprise-toggle').textContent = (surpriseOpen ? '^ ' : 'v ') + 'surprise';
    }

    function updateSurprise(entries, avg) {
      if (!entries || !entries.length) {
        surpriseTable.innerHTML = '<tr><td>no surprise entries yet</td></tr>'; return;
      }
      surpriseTable.innerHTML = entries.map(e => {
        const t = new Date(e.ts * 1000).toLocaleTimeString();
        return '<tr><td>' + t + ' ' + esc(e.content) + '</td></tr>';
      }).join('');
      const el = document.getElementById('surprise-avg');
      if (el && avg !== null && avg !== undefined) {
        el.textContent = 'D' + Number(avg).toFixed(2);
        el.className = avg < 0.2 ? 'low' : avg < 0.5 ? 'mid' : 'high';
      }
    }

    function updateRing(entries) {
      if (!entries || !entries.length) { ringTable.innerHTML = '<tr><td colspan="2">no ring entries</td></tr>'; return; }
      ringTable.innerHTML = entries.map(r => {
        const t = new Date(r.ts * 1000).toLocaleTimeString();
        return '<tr><td class="cat">[' + esc(r.category) + '] ' + t + '</td><td>' + esc(r.content) + '</td></tr>';
      }).join('');
    }

    function updateStatus(m) {
      const busy = m.busy === true;
      status.className = busy ? 'busy' : '';
      const tier  = m.tier  ? ' [' + m.tier + ']' : '';
      const inp = m.input ? ' -- "' + m.input + '"' : '';
      status.textContent = (busy ? '* ' : '  ') + (m.action || (busy ? 'processing' : 'idle')) + tier + inp;
    }

    function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

    function parseMarkdown(raw) {
      function fmt(s) {
        s = s.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
        return s;
      }
      const lines = raw.split('\n');
      const out = [];
      let inCode = false, codeLang = '', codeLines = [];
      let inUl = false, inOl = false;
      let paraLines = [];

      function flushPara() {
        if (!paraLines.length) return;
        out.push('<p>' + paraLines.join('<br>') + '</p>');
        paraLines = [];
      }
      function flushList() {
        if (inUl) { out.push('</ul>'); inUl = false; }
        if (inOl) { out.push('</ol>'); inOl = false; }
      }

      for (const line of lines) {
        if (line.startsWith('```')) {
          if (inCode) {
            out.push('<pre><code>' + esc(codeLines.join('\n')) + '</code></pre>');
            codeLines = []; inCode = false;
          } else {
            flushPara(); flushList();
            codeLang = line.slice(3).trim(); inCode = true;
          }
          continue;
        }
        if (inCode) { codeLines.push(line); continue; }
        if (!line.trim()) { flushPara(); flushList(); continue; }
        const hm = line.match(/^(#{1,3}) (.+)$/);
        if (hm) { flushPara(); flushList(); const lv = hm[1].length; out.push('<h' + lv + '>' + fmt(esc(hm[2])) + '</h' + lv + '>'); continue; }
        if (/^---+$/.test(line)) { flushPara(); flushList(); out.push('<hr>'); continue; }
        const bq = line.match(/^> (.+)$/);
        if (bq) { flushPara(); flushList(); out.push('<blockquote>' + fmt(esc(bq[1])) + '</blockquote>'); continue; }
        const ul = line.match(/^[ \t]*[-*] (.+)$/);
        if (ul) { flushPara(); if (!inUl) { flushList(); out.push('<ul>'); inUl = true; } out.push('<li>' + fmt(esc(ul[1])) + '</li>'); continue; }
        const ol = line.match(/^\d+\. (.+)$/);
        if (ol) { flushPara(); if (!inOl) { flushList(); out.push('<ol>'); inOl = true; } out.push('<li>' + fmt(esc(ol[1])) + '</li>'); continue; }
        flushList();
        paraLines.push(fmt(esc(line)));
      }
      flushPara(); flushList();
      if (inCode) out.push('<pre><code>' + esc(codeLines.join('\n')) + '</code></pre>');
      return out.join('\n');
    }

    function addMsg(cls, author, content) {
      const d = document.createElement('div');
      d.className = 'msg msg-' + cls;
      if (author) {
        const s = document.createElement('span');
        s.className = 'author'; s.textContent = author + ':'; d.appendChild(s);
      }
      const c = document.createElement(cls === 'igor' ? 'div' : 'span');
      if (cls === 'igor') { c.className = 'content md'; c.innerHTML = parseMarkdown(content); }
      else { c.className = 'content'; c.textContent = content; }
      d.appendChild(c);
      chat.appendChild(d);
      chat.scrollTop = chat.scrollHeight;
    }

    const led = document.getElementById('conn-led');
    let _connectedOnce = false, _disconnectedMsgShown = false, _retryDelay = 2000;

    function setLed(on) {
      led.classList.toggle('on', on); led.classList.toggle('off', !on);
      led.title = on ? 'Connected' : 'Disconnected';
    }

    function connect() {
      ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
      ws.onopen  = () => {
        setLed(true); _retryDelay = 2000;
        if (!_connectedOnce) { addMsg('system', '', 'Connected to Agentic Utility Closet.'); _connectedOnce = true; }
        else { addMsg('system', '', 'Reconnected.'); }
        _disconnectedMsgShown = false;
        const _cookieName = _loadName();
        if (_cookieName) ws.send(JSON.stringify({type: 'identify', name: _cookieName}));
        ws.send(JSON.stringify({type: 'join_session', session_id: currentSession}));
      };
      ws.onerror = () => { ws.close(); };
      ws.onclose = () => {
        setLed(false);
        if (!_disconnectedMsgShown) { addMsg('system', '', 'Disconnected. Retrying...'); _disconnectedMsgShown = true; }
        setTimeout(connect, _retryDelay);
        _retryDelay = Math.min(_retryDelay * 2, 30000);
      };
      ws.onmessage = e => {
        const m = JSON.parse(e.data);
        if (m.type === 'message') {
          const sid = m.session_id || 'shared';
          if (!sessionMsgs[sid]) sessionMsgs[sid] = [];
          sessionMsgs[sid].push(m);
          if (sessionMsgs[sid].length > 50) sessionMsgs[sid].shift();
          _renderSessionBar();
          if (sid === currentSession) {
            const cls = m.author === 'igor' ? 'igor' : m.author === 'claude-code' ? 'cc' : 'user';
            const label = m.author === 'igor' ? 'Igor' : m.author === 'claude-code' ? 'CC>' : (m.author || 'You');
            addMsg(cls, label, m.content);
          }
        } else if (m.type === 'session_history') {
          const sid = m.session_id || 'shared';
          sessionMsgs[sid] = m.messages || [];
          _renderSessionBar();
          if (sid === currentSession) _renderSession(sid);
        } else if (m.type === 'file_dropped')
          addMsg('system', '', 'clip ' + m.filename + ' received in inbox');
        else if (m.type === 'activity')
          updateStatus(m);
        else if (m.type === 'agent_status') {
          if (m.status === 'attached') _knownAgents.add(m.agent_id);
          else _knownAgents.delete(m.agent_id);
          agentStatus.textContent = m.agent_id + ': ' + m.status;
          agentStatus.className = m.status === 'attached' ? 'attached' : '';
          addMsg('system', '', m.agent_id + ' ' + m.status);
        } else if (m.type === 'platform_status') {
          const aa = m.attached_agents || [];
          _knownAgents.clear(); aa.forEach(a => _knownAgents.add(a));
          agentStatus.textContent = aa.length ? aa.join(', ') : 'no agent';
          agentStatus.className = aa.length ? 'attached' : '';
        } else if (m.type === 'platform_shutdown') {
          addMsg('system', '', 'Platform shutting down...');
        } else if (m.type === 'name_resolved') {
          senderName.value = m.name; _saveName(m.name);
          addMsg('system', '', 'Name learned: ' + m.name);
        }
      };
    }

    function sendMsg() {
      const rawText = input.value.trim();
      if (!rawText || !ws || ws.readyState !== 1) return;
      const name = (senderName.value.trim() || 'akien').toLowerCase();
      ws.send(JSON.stringify({type: 'message', content: rawText, author: name, session_id: currentSession}));
      input.value = '';
      if (ccEnabled) sendToBridge(rawText, 'shared');
    }
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
    });

    async function uploadFile(el) {
      const file = el.files[0]; if (!file) return;
      const fd = new FormData(); fd.append('file', file);
      const r = await fetch('/api/upload', {method: 'POST', body: fd});
      const j = await r.json();
      addMsg('system', '', 'clip ' + j.filename + ' uploaded to inbox');
      el.value = '';
    }

    document.addEventListener('dragenter', e => {
      if (e.dataTransfer.types.includes('Files')) { dragDepth++; overlay.classList.add('active'); }
    });
    document.addEventListener('dragleave', () => {
      if (--dragDepth <= 0) { dragDepth = 0; overlay.classList.remove('active'); }
    });
    document.addEventListener('dragover', e => e.preventDefault());
    document.addEventListener('drop', async e => {
      e.preventDefault(); dragDepth = 0; overlay.classList.remove('active');
      const file = e.dataTransfer.files[0]; if (!file) return;
      const fd = new FormData(); fd.append('file', file);
      const r = await fetch('/api/upload', {method: 'POST', body: fd});
      const j = await r.json();
      addMsg('system', '', 'clip ' + j.filename + ' dropped into inbox');
    });

    async function pollDash() {
      try {
        const r = await fetch('/api/dashboard');
        const d = await r.json();
        const toggle   = document.getElementById('ring-toggle');
        const stoggle  = document.getElementById('surprise-toggle');
        if (d.status === 'no agent attached') {
          dash.innerHTML = '<span>No agent attached</span>';
          dash.appendChild(toggle); dash.appendChild(stoggle);
          return;
        }
        // Generic: show agent name + any key stats the agent pushes
        const parts = [];
        if (d.agent) parts.push('[' + d.agent + ']');
        // Render all agent-pushed keys except internal ones
        const skip = new Set(['ts', 'agent', 'ring_recent', 'surprise_recent', 'surprise_avg']);
        for (const [k, v] of Object.entries(d)) {
          if (skip.has(k) || v === null || v === undefined) continue;
          if (typeof v === 'number') parts.push(k + ':' + (k.includes('cost') ? '$' + v.toFixed(4) : v));
          else if (typeof v === 'string') parts.push(k + ':' + v);
        }
        dash.innerHTML = (parts.length ? parts.map(p => '<span>' + esc(p) + '</span>').join('') : '<span>Online</span>');
        dash.appendChild(toggle); dash.appendChild(stoggle);
        if (d.ring_recent) updateRing(d.ring_recent);
        if (d.surprise_recent) updateSurprise(d.surprise_recent, d.surprise_avg);
      } catch(e) {}
    }

    let ccEnabled = false;
    function toggleCC() {
      ccEnabled = !ccEnabled;
      document.getElementById('bridge-pane').style.display = ccEnabled ? 'flex' : 'none';
      document.getElementById('cc-toggle').classList.toggle('active', ccEnabled);
    }

    function addBridgeMsg(cls, author, content) {
      const bc = document.getElementById('bridge-chat');
      const d = document.createElement('div'); d.className = 'msg msg-' + cls;
      if (author) { const s = document.createElement('span'); s.className = 'author'; s.textContent = author + ':'; d.appendChild(s); }
      const c = document.createElement(cls === 'claude' ? 'div' : 'span');
      if (cls === 'claude') { c.className = 'content md'; c.innerHTML = parseMarkdown(content); }
      else { c.className = 'content'; c.textContent = content; }
      d.appendChild(c); bc.appendChild(d); bc.scrollTop = bc.scrollHeight;
    }

    async function sendToBridge(message, channel) {
      if (channel === 'shared') addBridgeMsg('user', 'you', message);
      const thinkId = 'think-' + Date.now();
      const bc = document.getElementById('bridge-chat');
      const thinkEl = document.createElement('div');
      thinkEl.id = thinkId; thinkEl.className = 'msg msg-system';
      thinkEl.textContent = 'Claude is thinking...'; bc.appendChild(thinkEl);
      bc.scrollTop = bc.scrollHeight;
      try {
        const r = await fetch('/api/bridge_chat', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message, channel})
        });
        const j = await r.json();
        const el = document.getElementById(thinkId); if (el) el.remove();
        if (j.reply) {
          addBridgeMsg('claude', 'Claude', j.reply);
          const cnt = document.getElementById('bridge-count');
          if (cnt) cnt.textContent = j.message_count + ' msgs';
        } else { addBridgeMsg('system', '', 'Bridge error: ' + (j.error || 'unknown')); }
      } catch(e) {
        const el = document.getElementById(thinkId); if (el) el.remove();
        addBridgeMsg('system', '', 'Bridge unavailable: ' + e.message);
      }
    }

    async function sendBack() {
      const bi = document.getElementById('back-input');
      const msg = bi.value.trim(); if (!msg) return; bi.value = '';
      await sendToBridge(msg, 'back');
    }

    document.getElementById('back-input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendBack(); }
    });

    if (_urlSession !== 'shared') _renderSessionBar();
    connect();
    pollDash();
    setInterval(pollDash, 5000);
  </script>
</body>
</html>"""


if __name__ == "__main__":
    main()
