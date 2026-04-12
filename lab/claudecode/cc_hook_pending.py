#!/usr/bin/env python3
"""
cc_hook_pending.py — UserPromptSubmit hook for Claude Code.

T-cc-hook-igor-notify: Reads new messages from the SHARED channel (via
Postgres channel_messages table) since the last hook invocation and returns
them as additionalContext for CC to see before processing Akien's prompt.

Runs in two modes:
  - Hook mode: reads JSON from stdin, writes JSON response to stdout
  - CLI mode: --dry-run prints what would be injected

Skips entirely when CLAUDE_MINION=true is set — worker/minion CCs don't get
interrupted by SHARED channel traffic. The primary interactive CC session
gets the notifications.

Cursor tracking: stores last-seen message timestamp in a per-session file
at ~/.TheIgors/cc_hook_cursor_<session_id>.txt so multiple CC instances
don't step on each other.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CURSOR_DIR = Path.home() / ".TheIgors"
MAX_MESSAGES = 20  # Cap how much we inject — context budget discipline
MAX_CONTENT_CHARS = 400  # Per-message truncation


def _db_url():
    """Read Igor home DB URL from env or .env file."""
    url = os.environ.get("IGOR_HOME_DB_URL")
    if url:
        return url
    env_file = Path.home() / ".TheIgors" / "Igor-wild-0001" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("IGOR_HOME_DB_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001"


def _cursor_path(session_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)[:40]
    return CURSOR_DIR / f"cc_hook_cursor_{safe}.txt"


def _read_cursor(session_id: str) -> str:
    path = _cursor_path(session_id)
    if path.exists():
        return path.read_text().strip()
    # First run: start from "now" so we don't dump the full channel history
    return datetime.now(timezone.utc).isoformat()


def _write_cursor(session_id: str, ts: str) -> None:
    CURSOR_DIR.mkdir(parents=True, exist_ok=True)
    _cursor_path(session_id).write_text(ts)


def fetch_new_messages(session_id: str) -> tuple[list[dict], str]:
    """Return (messages_since_cursor, new_cursor_ts)."""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        return [], ""

    cursor_ts = _read_cursor(session_id)

    try:
        conn = psycopg2.connect(_db_url())
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT ts, author, type, content
            FROM channel_messages
            WHERE ts > %s
              AND author != 'claude-code'
            ORDER BY ts ASC
            LIMIT %s
            """,
            [cursor_ts, MAX_MESSAGES],
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception:
        return [], cursor_ts

    new_cursor = rows[-1]["ts"] if rows else cursor_ts
    return rows, new_cursor


def format_messages(rows: list[dict]) -> str:
    if not rows:
        return ""
    lines = [
        "--- NEW MESSAGES SINCE LAST TURN (from SHARED channel) ---",
    ]
    for r in rows:
        ts = str(r.get("ts", ""))[:19]  # YYYY-MM-DDTHH:MM:SS
        author = r.get("author", "?")
        content = (r.get("content") or "")[:MAX_CONTENT_CHARS]
        if len(r.get("content") or "") > MAX_CONTENT_CHARS:
            content += "…"
        lines.append(f"[{ts}] {author}: {content}")
    lines.append("--- end new messages ---")
    return "\n".join(lines)


def main():
    # Minion bypass: worker CCs don't get notifications
    if os.environ.get("CLAUDE_MINION", "").lower() in ("true", "1", "yes"):
        # Output empty response so CC doesn't append anything
        print(json.dumps({}))
        return

    # Dry-run mode for CLI testing
    if "--dry-run" in sys.argv:
        session_id = os.environ.get("CLAUDE_SESSION_ID", "dry-run")
        rows, new_cursor = fetch_new_messages(session_id)
        text = format_messages(rows)
        print(f"Would inject {len(rows)} messages, new cursor: {new_cursor}")
        if text:
            print(text)
        return

    # Hook mode: read JSON from stdin
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Malformed stdin — fail silent so CC proceeds normally
        print(json.dumps({}))
        return

    session_id = data.get("session_id", "unknown")

    rows, new_cursor = fetch_new_messages(session_id)
    text = format_messages(rows)

    if text:
        _write_cursor(session_id, new_cursor)
        response = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": text,
            }
        }
        print(json.dumps(response))
    else:
        # Nothing new — return empty response
        print(json.dumps({}))


if __name__ == "__main__":
    main()
