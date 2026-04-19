#!/usr/bin/env python3
"""
chat_log_formatter.py — Convert CC's JSONL transcripts to daily markdown.

Source: newest session in ~/.claude/projects/-home-akien-TheIgors/*.jsonl
Sink:   ~/TheIgors/claude_chat_logs/YYYY-MM-DD.md (append-only)
State:  ~/.TheIgors/claudecode/chat_log_state.json (session → last-uuid seen)

Invoked by a Claude Code Stop hook after every turn. Safe to run manually.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sys
from pathlib import Path

_PROJECT_DIR = Path.home() / ".claude/projects/-home-akien-TheIgors"
_OUT_DIR = Path.home() / "TheIgors/claude_chat_logs"
_STATE_FILE = Path.home() / ".TheIgors/claudecode/chat_log_state.json"

_SKIP_TYPES = {
    "permission-mode",
    "file-history-snapshot",
    "queue-operation",
    "last-prompt",
    "attachment",
    "system",
}


def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_state(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2))


def _newest_jsonl() -> Path | None:
    if not _PROJECT_DIR.exists():
        return None
    candidates = sorted(_PROJECT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def _local_date(ts_iso: str) -> str:
    dt = _dt.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    return dt.astimezone().strftime("%Y-%m-%d")


def _local_time(ts_iso: str) -> str:
    dt = _dt.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    return dt.astimezone().strftime("%H:%M")


def _summarize_tool(name: str, inp: dict) -> str:
    if name == "Bash":
        cmd = (inp.get("command", "") or "").replace("\n", " ")
        return f"🔧 Bash: `{cmd[:120]}`"
    if name in {"Read", "Edit", "Write", "Glob", "Grep"}:
        target = inp.get("file_path") or inp.get("path") or inp.get("pattern") or ""
        return f"🔧 {name}: `{target}`"
    if name == "Skill":
        return f"🔧 Skill: /{inp.get('skill', '?')} {inp.get('args', '')}".rstrip()
    short = json.dumps(inp, default=str)[:120]
    return f"🔧 {name}: `{short}`"


def _render_user(entry: dict) -> list[str]:
    msg = entry.get("message") or {}
    content = msg.get("content")
    ts = _local_time(entry["timestamp"])
    lines: list[str] = []
    if isinstance(content, str):
        text = content.strip()
        if not text:
            return lines
        lines.append(f"## Akien [{ts}]\n")
        lines.append(text)
        lines.append("")
        return lines
    if isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_result":
                raw = c.get("content", "")
                if isinstance(raw, list):
                    raw = " ".join(
                        b.get("text", "") for b in raw if isinstance(b, dict)
                    )
                snippet = (raw or "").replace("\n", " ").strip()[:140]
                if snippet:
                    lines.append(f"    ↳ result: {snippet}")
    return lines


def _render_assistant(entry: dict) -> list[str]:
    msg = entry.get("message") or {}
    content = msg.get("content") or []
    ts = _local_time(entry["timestamp"])
    lines: list[str] = []
    header_written = False
    for c in content:
        if not isinstance(c, dict):
            continue
        t = c.get("type")
        if t == "text":
            text = (c.get("text") or "").strip()
            if not text:
                continue
            if not header_written:
                lines.append(f"## CC [{ts}]\n")
                header_written = True
            lines.append(text)
            lines.append("")
        elif t == "tool_use":
            if not header_written:
                lines.append(f"## CC [{ts}]\n")
                header_written = True
            lines.append(_summarize_tool(c.get("name", "?"), c.get("input") or {}))
        # skip "thinking" blocks per ticket
    return lines


def _append_by_day(by_day: dict[str, list[str]]) -> None:
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    for day, lines in by_day.items():
        path = _OUT_DIR / f"{day}.md"
        new_file = not path.exists()
        with path.open("a") as f:
            if new_file:
                f.write(f"# Claude Code chat log — {day}\n\n")
            f.write("\n".join(lines))
            if lines and not lines[-1].endswith("\n"):
                f.write("\n")


def main() -> int:
    jsonl = _newest_jsonl()
    if jsonl is None:
        return 0
    state = _load_state()
    session_id = jsonl.stem
    last_uuid = state.get(session_id)
    by_day: dict[str, list[str]] = {}
    newest_uuid = last_uuid
    seen_last = last_uuid is None  # if no cursor, start from beginning

    with jsonl.open() as f:
        for line in f:
            try:
                entry = json.loads(line)
            except Exception:
                continue
            uuid = entry.get("uuid")
            t = entry.get("type")
            if t in _SKIP_TYPES:
                continue
            if not seen_last:
                if uuid == last_uuid:
                    seen_last = True
                continue
            ts = entry.get("timestamp")
            if not ts:
                continue
            day = _local_date(ts)
            rendered: list[str] = []
            if t == "user":
                rendered = _render_user(entry)
            elif t == "assistant":
                rendered = _render_assistant(entry)
            if rendered:
                by_day.setdefault(day, []).extend(rendered)
            if uuid:
                newest_uuid = uuid

    if by_day:
        _append_by_day(by_day)
    if newest_uuid and newest_uuid != last_uuid:
        state[session_id] = newest_uuid
        _save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
