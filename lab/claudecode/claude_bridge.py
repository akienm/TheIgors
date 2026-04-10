#!/usr/bin/env python3
"""
claude_bridge.py — Persistent Claude API bridge service (D105).

Standalone Starlette service on port 8085.
Provides a persistent Claude conversation that survives Igor restarts.

Endpoints:
  POST /chat    {"message": "...", "channel": "shared|back"} → {reply, channel, ts, message_count}
  GET  /health  → {status, message_count, model}
  POST /compact → explicitly compact history (summarize → seed+summary)

Channels:
  shared — message is part of the three-way Akien+Igor+Claude chat.
            Claude responds in the bridge pane; Igor responds via his own loop.
  back   — message goes to Claude only; Igor never sees it.

History:
  Persisted to ~/.TheIgors/claude_bridge_history.json
  Auto-compact at AUTO_COMPACT_THRESHOLD messages (summarize → fresh seed + summary)

Context seed (on startup / after compact):
  - CLAUDE.md project conventions
  - Active PROCEDURAL habits from Igor's DB (up to 30)
  - gap_analysis.md current gaps
  - Last 100 lines of most recent BG log
  - Brief mission framing

Run from repo root:
  python claudecode/claude_bridge.py

Or via cron (@reboot, after a short delay so Igor has time to start).
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO = Path(__file__).parent.parent
INSTANCE_DIR = Path.home() / ".TheIgors" / "Igor-wild-0001"
HISTORY_FILE = Path.home() / ".TheIgors" / "claude_bridge_history.json"
LOG_DIR = Path.home() / ".TheIgors" / "logs"
LOG_FILE = LOG_DIR / "claude_bridge.log"
GAP_ANALYSIS = REPO / "design_docs" / "gap_analysis.md"
CLAUDE_MD = REPO / "CLAUDE.md"
IGOR_HOME_DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)

# ── Config ─────────────────────────────────────────────────────────────────────
BRIDGE_PORT = int(os.environ.get("CLAUDE_BRIDGE_PORT", "8085"))
MODEL = "claude-sonnet-4-6"
AUTO_COMPACT_THRESHOLD = 40  # user+assistant message pairs trigger compact
MAX_BG_LOG_LINES = 100

# ── Anthropic client ───────────────────────────────────────────────────────────
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("REAL_ANTHROPIC_API_KEY") or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        if not api_key:
            raise RuntimeError(
                "No Anthropic API key found. Set REAL_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── Logging ────────────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"{ts}  {msg}\n"
    print(line, end="", flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass


# ── History persistence ────────────────────────────────────────────────────────


def _load_history() -> list:
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text())
    except Exception:
        pass
    return []


def _save_history(history: list) -> None:
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except Exception as e:
        _log(f"WARN: could not save history: {e}")


# ── Context seed ───────────────────────────────────────────────────────────────


def _read_habits_from_db(limit: int = 30) -> str:
    """Pull PROCEDURAL habits from Igor's DB for context seeding."""
    try:
        import psycopg2

        conn = psycopg2.connect(IGOR_HOME_DB_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, narrative, metadata FROM memories"
            " WHERE memory_type = 'PROCEDURAL'"
            " ORDER BY inertia DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        lines = []
        for mid, narr, meta_json in rows:
            try:
                meta = json.loads(meta_json or "{}")
            except Exception:
                meta = {}
            trigger = meta.get("trigger", "")
            habit_type = meta.get("habit_type", "")
            lines.append(
                f"  [{mid}] ({habit_type}) trigger={trigger!r}\n  {narr[:120]}"
            )
        return "\n".join(lines) if lines else "(no habits found)"
    except Exception as e:
        return f"(could not read habits: {e})"


def _read_bg_log_tail(n: int = MAX_BG_LOG_LINES) -> str:
    """Return last N lines of the most recent BG log."""
    try:
        bg_logs = sorted(
            LOG_DIR.glob("bg_job_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not bg_logs:
            return "(no BG logs found)"
        lines = bg_logs[0].read_text(errors="replace").splitlines()
        tail = lines[-n:] if len(lines) > n else lines
        return "\n".join(tail)
    except Exception as e:
        return f"(could not read BG log: {e})"


def _build_seed_context() -> str:
    """Build the system prompt injected at session start and after compact."""
    claude_md = "(CLAUDE.md not readable)"
    try:
        if CLAUDE_MD.exists():
            claude_md = CLAUDE_MD.read_text(errors="replace")[:8000]
    except Exception:
        pass

    gap_analysis = "(gap_analysis.md not readable)"
    try:
        if GAP_ANALYSIS.exists():
            gap_analysis = GAP_ANALYSIS.read_text(errors="replace")[:4000]
    except Exception:
        pass

    habits = _read_habits_from_db()
    bg_log = _read_bg_log_tail()

    return (
        "You are Claude Code running as a persistent bridge in the TheIgors project.\n"
        "You are participating in a shared three-way conversation with Akien (the human)\n"
        "and Igor (the AI agent running at localhost:8080).\n\n"
        "Your role: habit calibration, design work, code analysis, and code changes.\n"
        "When a message is labeled [shared], Igor also received it and is responding.\n"
        "When a message is labeled [back], only you see it — Igor is not in this exchange.\n"
        "Reply naturally. Do not prefix your responses with labels.\n\n"
        f"PROJECT CONVENTIONS (CLAUDE.md, first 8000 chars):\n{claude_md}\n\n"
        f"CURRENT OPEN GAPS (gap_analysis.md, first 4000 chars):\n{gap_analysis}\n\n"
        f"IGOR'S ACTIVE HABITS (from DB):\n{habits}\n\n"
        f"RECENT BACKGROUND LOGS (last {MAX_BG_LOG_LINES} lines of most recent bg_job log):\n"
        f"{bg_log}\n"
    )


# ── Session state (module-level, survives request boundary) ───────────────────
_history: list = []  # [{"role": "user"|"assistant", "content": "..."}, ...]
_system_prompt: str = ""


def _initialize_session() -> None:
    """Load persisted history or start fresh with seed context."""
    global _history, _system_prompt
    _system_prompt = _build_seed_context()
    loaded = _load_history()
    if loaded:
        _history = loaded
        _log(f"claude_bridge: resumed, {len(_history)} messages loaded from history")
    else:
        _history = []
        _log("claude_bridge: starting fresh session")


# ── Compact ────────────────────────────────────────────────────────────────────


def _compact_history() -> str:
    """Summarize history, reset to seed+summary. Returns the summary text."""
    global _history, _system_prompt
    if not _history:
        return "(nothing to compact)"

    _log(f"claude_bridge: compacting {len(_history)} messages")
    summary = "(compact summary not available)"
    try:
        client = _get_client()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=_system_prompt,
            messages=_history
            + [
                {
                    "role": "user",
                    "content": (
                        "Please write a concise summary of our conversation so far: "
                        "decisions made, problems diagnosed, code written or planned, "
                        "and the current in-flight hypothesis. "
                        "This summary will open the next session so we can continue seamlessly."
                    ),
                }
            ],
        )
        summary = resp.content[0].text
    except Exception as e:
        summary = f"(compact failed: {e})"

    # Rebuild: fresh seed + summary pair
    _system_prompt = _build_seed_context()
    _history = [
        {
            "role": "user",
            "content": f"[Session compact — prior conversation summary]\n{summary}",
        },
        {
            "role": "assistant",
            "content": "Got it — prior context loaded. Ready to continue.",
        },
    ]
    _save_history(_history)
    _log(f"claude_bridge: compacted → {len(_history)} messages")
    return summary


# ── Igor forwarding ───────────────────────────────────────────────────────────

IGOR_WEB_PORT = int(os.environ.get("IGOR_WEB_PORT", "8080"))


async def _forward_to_igor(reply: str) -> None:
    """POST Claude's reply to Igor's /api/cc_send so he sees it (shared channel only)."""
    import urllib.request as _ur

    payload = json.dumps({"content": f"[claude] {reply}"}).encode()

    def _post():
        try:
            req = _ur.Request(
                f"http://localhost:{IGOR_WEB_PORT}/api/cc_send",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            _ur.urlopen(req, timeout=5)
        except Exception as e:
            _log(f"WARN: _forward_to_igor failed: {e}")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _post)


# ── Route handlers ─────────────────────────────────────────────────────────────


async def _api_chat(request: Request) -> JSONResponse:
    """POST /chat {"message": "...", "channel": "shared|back"} → reply."""
    global _history

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    message = (body.get("message") or "").strip()
    channel = (body.get("channel") or "shared").strip().lower()
    if channel not in ("shared", "back"):
        channel = "shared"
    if not message:
        return JSONResponse({"error": "message required"}, status_code=400)

    # Auto-compact if threshold reached
    if len(_history) >= AUTO_COMPACT_THRESHOLD:
        _log(f"claude_bridge: auto-compact at {len(_history)} messages")
        _compact_history()

    # Label message for Claude's context awareness
    labelled = f"[{channel}] {message}"
    _history.append({"role": "user", "content": labelled})

    ts = datetime.now().isoformat(timespec="seconds")
    try:
        client = _get_client()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=_system_prompt,
            messages=_history,
        )
        reply = resp.content[0].text
        _history.append({"role": "assistant", "content": reply})
        _save_history(_history)
        _log(
            f"claude_bridge: {channel} [{len(_history)} msgs] "
            f"in={message[:60]!r} out={reply[:60]!r}"
        )
        # Shared channel: forward Claude's reply to Igor's UI so he can see it
        if channel == "shared":
            asyncio.ensure_future(_forward_to_igor(reply))
        return JSONResponse(
            {
                "reply": reply,
                "channel": channel,
                "ts": ts,
                "message_count": len(_history),
            }
        )
    except Exception as e:
        # Remove the user message we added since we didn't get a reply
        _history.pop()
        _log(f"claude_bridge: ERROR calling Claude: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def _api_health(request: Request) -> JSONResponse:
    """GET /health → {status, message_count, model, auto_compact_threshold}"""
    return JSONResponse(
        {
            "status": "ok",
            "message_count": len(_history),
            "model": MODEL,
            "auto_compact_threshold": AUTO_COMPACT_THRESHOLD,
        }
    )


async def _api_compact(request: Request) -> JSONResponse:
    """POST /compact → explicitly compact history. Returns summary."""
    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(None, _compact_history)
    return JSONResponse(
        {
            "status": "compacted",
            "summary": summary,
            "message_count": len(_history),
        }
    )


# ── App factory ────────────────────────────────────────────────────────────────


def _make_app() -> Starlette:
    routes = [
        Route("/chat", _api_chat, methods=["POST"]),
        Route("/health", _api_health, methods=["GET"]),
        Route("/compact", _api_compact, methods=["POST"]),
    ]
    return Starlette(routes=routes)


# ── Entry point ────────────────────────────────────────────────────────────────


def main() -> None:
    _initialize_session()
    _log(f"claude_bridge: starting on port {BRIDGE_PORT}, model={MODEL}")
    app = _make_app()
    config = uvicorn.Config(app, host="0.0.0.0", port=BRIDGE_PORT, log_level="warning")
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
