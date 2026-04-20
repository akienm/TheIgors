#!/usr/bin/env python3
"""
export_chat.py — Render CC session transcript(s) to markdown.

Usage:
    export_chat.py              — render the most-recently-modified transcript
                                  to claude_chat_logs/YYYYMMDD.md (today's date)
    export_chat.py --session <session-id>
                                — render a specific session
    export_chat.py --all        — render every transcript in the projects dir
                                  to its corresponding day (idempotent; appends if
                                  output file already exists)
    export_chat.py --dry-run    — print what would be written, don't touch disk

Source:  ~/.claude/projects/-home-akien-TheIgors/<session-id>.jsonl
Output:  /home/akien/TheIgors/claude_chat_logs/YYYYMMDD.md

Recovery purpose — if something scrolls off the top of the chat, run
/export-chat to get a persistent copy.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRANSCRIPT_DIR = Path.home() / ".claude/projects/-home-akien-TheIgors"
OUTPUT_DIR = Path("/home/akien/TheIgors/claude_chat_logs")


def _render_message(msg: dict) -> str:
    """Render one transcript message to markdown. Returns '' for uninteresting ones."""
    mtype = msg.get("type")
    ts = msg.get("timestamp", "")
    if mtype == "user":
        # user messages can have nested structure
        content = msg.get("message", {}).get("content", "")
        if isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict):
                    if c.get("type") == "text":
                        parts.append(c.get("text", ""))
                    elif c.get("type") == "tool_result":
                        # elide tool results — too noisy for a recovery log
                        tc = c.get("content", "")
                        if isinstance(tc, list):
                            tc = " ".join(
                                p.get("text", "") for p in tc if isinstance(p, dict)
                            )
                        elide = str(tc)[:200].replace("\n", " ")
                        parts.append(
                            f"_[tool result: {elide}{'...' if len(str(tc)) > 200 else ''}]_"
                        )
                elif isinstance(c, str):
                    parts.append(c)
            content = "\n".join(p for p in parts if p)
        if not content:
            return ""
        return f"\n### User — {ts}\n\n{content}\n"
    if mtype == "assistant":
        msg_body = msg.get("message", {})
        content = msg_body.get("content", "")
        if isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict):
                    if c.get("type") == "text":
                        parts.append(c.get("text", ""))
                    elif c.get("type") == "tool_use":
                        tname = c.get("name", "?")
                        tin = c.get("input", {})
                        # render a one-line summary of the tool call
                        summary = json.dumps(tin)[:200].replace("\n", " ")
                        parts.append(
                            f"_[tool: {tname}({summary}{'...' if len(json.dumps(tin)) > 200 else ''})]_"
                        )
            content = "\n".join(p for p in parts if p)
        elif not isinstance(content, str):
            return ""
        if not content:
            return ""
        return f"\n### Assistant — {ts}\n\n{content}\n"
    return ""


def _date_for_transcript(path: Path) -> str:
    """Derive YYYYMMDD from transcript's first message timestamp, else mtime."""
    try:
        with path.open() as f:
            first = f.readline()
            if first:
                obj = json.loads(first)
                ts = obj.get("timestamp")
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return dt.astimezone().strftime("%Y-%m-%d")
    except Exception:
        pass
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime.strftime("%Y-%m-%d")


def render(path: Path) -> str:
    """Render one transcript file to markdown."""
    lines = []
    lines.append(f"# Chat log — {path.name}\n")
    lines.append(f"_rendered {datetime.now(timezone.utc).isoformat()}_\n")
    msg_count = 0
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            rendered = _render_message(msg)
            if rendered:
                lines.append(rendered)
                msg_count += 1
    lines.append(f"\n---\n_{msg_count} messages rendered_\n")
    return "".join(lines)


def write_out(path: Path, content: str, date_str: str, dry_run: bool) -> Path:
    out_path = OUTPUT_DIR / f"{date_str}.md"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"[dry-run] would write {len(content)} bytes → {out_path}")
        return out_path
    separator = ""
    mode = "w"
    if out_path.exists():
        # append with separator so multiple sessions on the same day stack
        separator = f"\n\n---\n\n## Additional session transcript {path.name}\n"
        mode = "a"
    with out_path.open(mode) as f:
        f.write(separator + content)
    print(f"Wrote {len(content)} bytes → {out_path}")
    return out_path


def resolve_target(session_id: str | None, all_mode: bool) -> list[Path]:
    if all_mode:
        files = sorted(TRANSCRIPT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not files:
            print("No transcripts found.", file=sys.stderr)
            sys.exit(1)
        return files
    if session_id:
        p = TRANSCRIPT_DIR / f"{session_id}.jsonl"
        if not p.exists():
            print(f"No transcript for session {session_id}", file=sys.stderr)
            sys.exit(1)
        return [p]
    # default: most-recently-modified transcript
    files = sorted(TRANSCRIPT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not files:
        print("No transcripts found.", file=sys.stderr)
        sys.exit(1)
    return [files[-1]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="Specific session id (without .jsonl)")
    parser.add_argument("--all", action="store_true", help="Render every transcript")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = resolve_target(args.session, args.all)
    for p in targets:
        content = render(p)
        date_str = _date_for_transcript(p)
        write_out(p, content, date_str, args.dry_run)


if __name__ == "__main__":
    main()
