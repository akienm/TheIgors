"""
map_igor.py — On-demand inspection snapshot of Igor's full state.

Produces ~/.TheIgors/maps/igor-map-<YYYY-MM-DD-HHMMSS>.json plus a
one-screen stdout summary. Invoked by /map-igor skill.

Sections: palace_tree, rules, subsystem_index, tickets, slates, decisions,
gates, mcp_servers, imap_buses, channels, inbox, logs, startup_reads,
db_schema, runtime, code_map, processes.

Diff mode: --since=yesterday compares against the prior map.
Section mode: --section=<name> runs only one collector.

Updated 2026-04-29T00:00:00Z
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wild_igor.igor.igor_base import IgorBase

_DB_URL = os.environ["IGOR_HOME_DB_URL"]
_SEARCH_PATH = os.environ.get("IGOR_HOME_SEARCH_PATH") or "clan,infra,public"
_HOME = Path.home()
_IGOR_HOME = _HOME / ".TheIgors" / "Igor-wild-0001"
_MAPS_DIR = _HOME / ".TheIgors" / "maps"
_REPO = _HOME / "TheIgors"

MAP_TTL_DAYS = 14


class IgorMap(IgorBase):
    """Produces a structured snapshot of Igor's full state."""

    def __init__(self, sections: list[str] | None = None):
        super().__init__()
        self.sections = sections
        self._snapshot: dict[str, Any] = {}

    def _run(self, cmd: str, timeout: int = 10) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return (result.stdout + result.stderr).strip()[:2000]
        except Exception as e:
            return f"[ERROR] {e}"

    def _pg(self, sql: str) -> list[tuple]:
        try:
            import psycopg2

            conn = psycopg2.connect(_DB_URL)
            cur = conn.cursor()
            cur.execute(f"SET search_path TO {_SEARCH_PATH}")
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            return [("ERROR", str(e))]

    def collect_palace_tree(self) -> dict:
        rows = self._pg(
            "SELECT path, title, LENGTH(content) FROM memory_palace ORDER BY path LIMIT 500"
        )
        return {
            "total_nodes": len(rows),
            "nodes": [
                {"path": r[0], "title": r[1], "content_bytes": r[2]} for r in rows[:100]
            ],
        }

    def collect_rules(self) -> dict:
        rows = self._pg(
            "SELECT path, title, content FROM memory_palace WHERE path LIKE 'theigors/rules/%' ORDER BY path"
        )
        return {r[0]: {"title": r[1], "content": r[2][:500]} for r in rows}

    def collect_subsystem_index(self) -> dict:
        rows = self._pg(
            "SELECT content FROM memory_palace WHERE path = 'theigors/subsystem_index'"
        )
        return {"content": rows[0][0][:2000] if rows else "(not found)"}

    def collect_tickets(self) -> dict:
        try:
            import sys as _sys

            _sys.path.insert(0, str(_REPO / "lab" / "claudecode"))
            from cc_queue import load_tasks

            tasks = load_tasks()
        except Exception as e:
            return {"error": str(e)}
        by_status: dict[str, list] = {}
        for t in tasks:
            s = t.get("status", "unknown")
            by_status.setdefault(s, []).append(
                {
                    "id": t["id"],
                    "title": t.get("title", "")[:80],
                    "size": t.get("size", "?"),
                    "gate": t.get("gate", ""),
                }
            )
        return {s: items for s, items in sorted(by_status.items())}

    def collect_slates(self) -> dict:
        slate_dir = _HOME / ".TheIgors" / "claudecode"
        slates = (
            sorted(slate_dir.glob("*.slate.txt"), reverse=True)[:4]
            if slate_dir.exists()
            else []
        )
        result = {}
        for s in slates:
            try:
                result[s.stem] = s.read_text()[:1000]
            except Exception:
                pass
        return result

    def collect_decisions(self) -> dict:
        log = _REPO / "lab" / "design_docs_for_igor" / "decisions_log.dsb"
        if not log.exists():
            return {"error": "not found"}
        lines = log.read_text().splitlines()
        return {"last_30": lines[-30:]}

    def collect_gates(self) -> dict:
        cfg = _IGOR_HOME / "igor.switches.cfg"
        if not cfg.exists():
            return {"error": "not found"}
        gates = {}
        for line in cfg.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                gates[k.strip()] = v.strip()
        return gates

    def collect_mcp_servers(self) -> dict:
        settings = _HOME / ".claude" / "settings.json"
        if not settings.exists():
            return {}
        try:
            data = json.loads(settings.read_text())
            return data.get("mcpServers", {})
        except Exception:
            return {}

    def collect_channels(self) -> dict:
        ch_dir = _HOME / ".TheIgors" / "cc_channel"
        result = {}
        msgs = ch_dir / "messages.jsonl"
        if msgs.exists():
            lines = msgs.read_text().splitlines()
            result["message_count"] = len(lines)
            result["last_5"] = lines[-5:]
        return result

    def collect_inbox(self) -> dict:
        inbox = _HOME / ".TheIgors" / "cc_inbox.jsonl"
        if not inbox.exists():
            return {"unread": 0}
        try:
            entries = [
                json.loads(l) for l in inbox.read_text().splitlines() if l.strip()
            ]
            unread = [e for e in entries if not e.get("read")]
            return {
                "unread": len(unread),
                "by_urgency": {
                    "high": sum(1 for e in unread if e.get("urgency") == "high"),
                    "normal": sum(
                        1 for e in unread if e.get("urgency") not in ("high", "low")
                    ),
                    "low": sum(1 for e in unread if e.get("urgency") == "low"),
                },
                "latest": unread[:3],
            }
        except Exception as e:
            return {"error": str(e)}

    def collect_logs(self) -> dict:
        result = {}
        for log_path in sorted((_HOME / ".TheIgors").rglob("*.log")):
            try:
                stat = log_path.stat()
                result[str(log_path)] = {
                    "size_mb": round(stat.st_size / 1_048_576, 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                }
            except Exception:
                pass
        return result

    def collect_db_schema(self) -> dict:
        rows = self._pg("""SELECT relname, n_live_tup FROM pg_stat_user_tables
               WHERE schemaname IN ('clan','infra','instance')
               ORDER BY n_live_tup DESC LIMIT 30""")
        return {"tables": [{"table": r[0], "rows": r[1]} for r in rows]}

    def collect_runtime(self) -> dict:
        return {
            "du": self._run(
                f"du -sh {_HOME / '.TheIgors'}/* 2>/dev/null | sort -rh | head -10"
            )
        }

    def collect_code_map(self) -> dict:
        result = {}
        igor_src = _REPO / "wild_igor" / "igor"
        if igor_src.exists():
            for d in sorted(igor_src.iterdir()):
                if d.is_dir() and not d.name.startswith("_"):
                    py_files = list(d.glob("*.py"))
                    result[d.name] = [f.name for f in sorted(py_files)[:5]]
        return result

    def collect_processes(self) -> dict:
        return {
            "tmux": self._run("tmux ls 2>/dev/null"),
            "igor_pids": self._run(
                "pgrep -a -f 'wild_igor|igor.*main' 2>/dev/null | head -5"
            ),
            "ollama": self._run("pgrep -a -f ollama 2>/dev/null | head -3"),
        }

    _COLLECTORS = {
        "palace_tree": collect_palace_tree,
        "rules": collect_rules,
        "subsystem_index": collect_subsystem_index,
        "tickets": collect_tickets,
        "slates": collect_slates,
        "decisions": collect_decisions,
        "gates": collect_gates,
        "mcp_servers": collect_mcp_servers,
        "channels": collect_channels,
        "inbox": collect_inbox,
        "logs": collect_logs,
        "db_schema": collect_db_schema,
        "runtime": collect_runtime,
        "code_map": collect_code_map,
        "processes": collect_processes,
    }

    def collect(self) -> dict[str, Any]:
        targets = self.sections or list(self._COLLECTORS.keys())
        snapshot: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sections": {},
        }
        for name in targets:
            fn = self._COLLECTORS.get(name)
            if fn:
                try:
                    snapshot["sections"][name] = fn(self)
                except Exception as e:
                    snapshot["sections"][name] = {"error": str(e)}
        self._snapshot = snapshot
        return snapshot

    def save(self, snapshot: dict) -> Path:
        _MAPS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        out = _MAPS_DIR / f"igor-map-{ts}.json"
        out.write_text(json.dumps(snapshot, indent=2, default=str))
        # Expire old maps
        for old in sorted(_MAPS_DIR.glob("igor-map-*.json"))[:-MAP_TTL_DAYS]:
            try:
                old.unlink()
            except Exception:
                pass
        return out

    def render_summary(self, snapshot: dict) -> str:
        secs = snapshot.get("sections", {})
        lines = [f"Igor map — {snapshot.get('generated_at', '?')}"]
        if "palace_tree" in secs:
            lines.append(
                f"  palace: {secs['palace_tree'].get('total_nodes', '?')} nodes"
            )
        if "tickets" in secs:
            t = secs["tickets"]
            lines.append(
                f"  tickets: {len(t.get('pending', []))} pending, {len(t.get('in_progress', []))} in_progress, {len(t.get('done', []))} done"
            )
        if "gates" in secs:
            enabled = [
                k for k, v in secs["gates"].items() if v.lower() in ("true", "1", "yes")
            ]
            lines.append(f"  gates enabled: {', '.join(enabled) or 'none'}")
        if "inbox" in secs:
            lines.append(f"  inbox: {secs['inbox'].get('unread', 0)} unread")
        if "processes" in secs:
            lines.append(f"  tmux: {secs['processes'].get('tmux', '?')[:80]}")
        if "logs" in secs:
            big = [
                (p, d["size_mb"])
                for p, d in secs["logs"].items()
                if d.get("size_mb", 0) > 5
            ]
            if big:
                lines.append(
                    f"  LARGE LOGS: {', '.join(f'{p}({m}MB)' for p,m in big[:3])}"
                )
        return "\n".join(lines)


def diff_snapshots(current: dict, prior: dict) -> dict:
    """Return sections where current differs from prior."""
    diff = {}
    for section in current.get("sections", {}):
        cur_val = json.dumps(current["sections"][section], sort_keys=True)
        pri_val = json.dumps(prior.get("sections", {}).get(section, {}), sort_keys=True)
        if cur_val != pri_val:
            diff[section] = {
                "current": current["sections"][section],
                "prior": prior.get("sections", {}).get(section),
            }
    return diff


def main():
    parser = argparse.ArgumentParser(description="Igor state snapshot")
    parser.add_argument("--section", help="Run only this section")
    parser.add_argument("--since", help="Diff against prior map (e.g. yesterday)")
    args = parser.parse_args()

    sections = [args.section] if args.section else None
    mapper = IgorMap(sections=sections)
    snapshot = mapper.collect()
    out = mapper.save(snapshot)

    if args.since and _MAPS_DIR.exists():
        prior_maps = sorted(_MAPS_DIR.glob("igor-map-*.json"))
        if len(prior_maps) >= 2:
            prior = json.loads(prior_maps[-2].read_text())
            diff = diff_snapshots(snapshot, prior)
            print(f"Diff vs prior map ({prior_maps[-2].name}):")
            print(f"  {len(diff)} sections changed: {', '.join(diff.keys())}")

    print(mapper.render_summary(snapshot))
    print(f"\nFull snapshot: {out}")


if __name__ == "__main__":
    main()
