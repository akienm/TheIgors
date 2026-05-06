#!/usr/bin/env python3
# author-model: sonnet
"""
cc_log_stop_hook.py — Stop hook driver: ingest CC session transcript via ChatLogHandler.

Finds the most-recently-modified CC session JSONL across all project dirs,
ingests it through ChatLogHandler, and flushes to date-partitioned markdown at
~/.agent_datacenter/logs/CC.0/YYYY-MM-DD.md.

Replaces chat_log_formatter.py. Safe to run manually.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _newest_jsonl() -> Path | None:
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None
    candidates = sorted(
        projects_dir.glob("*/*.jsonl"),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def main() -> int:
    jsonl = _newest_jsonl()
    if jsonl is None:
        return 0
    try:
        from devices.claude.chat_log_handler import ChatLogHandler, ingest_session
    except ImportError as e:
        print(f"cc_log_stop_hook: import failed ({e})", file=sys.stderr)
        return 1
    handler = ChatLogHandler()
    ingest_session(jsonl, handler)
    handler.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
