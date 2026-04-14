#!/usr/bin/env python3
"""
audit_add.py — T-audit-add-checks (#446)

CLI for registering audit checks that the audit skill picks up at sweep time.

Two add modes:
  - next      one-shot — runs in the next audit sweep, then auto-cleared
  - forever   persistent — runs in every audit sweep going forward

Storage: lab/claudecode/audit_checks.json. Two top-level lists: next_sweep
(drained after each audit run) and forever (persistent). Each entry has
{name, kind, pattern, description, severity, added_by, added_at, ack_until}.

Kinds:
  grep     regex/literal search across wild_igor/ source via Grep tool
  sql      psql query against the home DB
  python   inline Python expression against the codebase or DB
  shell    bash one-liner

Usage:
  audit_add.py add next "name" --kind grep --pattern 'PATTERN' [--desc TEXT] [--sev high|med|low]
  audit_add.py add forever "name" --kind sql --pattern 'SELECT ...' [--desc TEXT]
  audit_add.py list
  audit_add.py rm "name"
  audit_add.py ack "name" --until 2026-04-30
  audit_add.py drain      # called by audit skill — moves next_sweep entries to history
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "audit_checks.json"


def _load() -> dict:
    if not REGISTRY_PATH.exists():
        return {"next_sweep": [], "forever": [], "history": []}
    return json.loads(REGISTRY_PATH.read_text())


def _save(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n")


def _now() -> str:
    return datetime.now().isoformat()


def _entry(
    name: str, kind: str, pattern: str, description: str, severity: str, mode: str
) -> dict:
    return {
        "name": name,
        "kind": kind,
        "pattern": pattern,
        "description": description or "",
        "severity": severity,
        "added_by": "claude-code",
        "added_at": _now(),
        "mode": mode,
        "ack_until": None,
    }


def cmd_add(args) -> int:
    data = _load()
    target = "next_sweep" if args.mode == "next" else "forever"
    existing = next((e for e in data[target] if e["name"] == args.name), None)
    if existing:
        print(
            f"check '{args.name}' already registered in {target} — use rm first or pick a different name",
            file=sys.stderr,
        )
        return 1
    data[target].append(
        _entry(
            args.name,
            args.kind,
            args.pattern,
            args.description or "",
            args.severity,
            args.mode,
        )
    )
    _save(data)
    print(f"registered {args.mode} check: {args.name} ({args.kind})")
    return 0


def cmd_list(args) -> int:
    data = _load()
    print(f"=== forever ({len(data['forever'])}) ===")
    for e in data["forever"]:
        ack = f" [ack until {e['ack_until']}]" if e.get("ack_until") else ""
        print(f"  {e['name']:<40} {e['kind']:<8} sev={e['severity']:<6}{ack}")
        if e.get("description"):
            print(f"    {e['description'][:100]}")
    print()
    print(f"=== next_sweep ({len(data['next_sweep'])}) ===")
    for e in data["next_sweep"]:
        print(f"  {e['name']:<40} {e['kind']:<8} sev={e['severity']:<6}")
        if e.get("description"):
            print(f"    {e['description'][:100]}")
    print()
    print(f"=== history ({len(data['history'])}) === (last 5)")
    for e in data["history"][-5:]:
        print(f"  {e['name']:<40} ran_at={e.get('ran_at', '?')}")
    return 0


def cmd_rm(args) -> int:
    data = _load()
    removed = 0
    for bucket in ("forever", "next_sweep"):
        before = len(data[bucket])
        data[bucket] = [e for e in data[bucket] if e["name"] != args.name]
        removed += before - len(data[bucket])
    if removed == 0:
        print(f"no check named '{args.name}' found", file=sys.stderr)
        return 1
    _save(data)
    print(f"removed {removed} check(s) named '{args.name}'")
    return 0


def cmd_ack(args) -> int:
    data = _load()
    found = False
    for bucket in ("forever", "next_sweep"):
        for e in data[bucket]:
            if e["name"] == args.name:
                e["ack_until"] = args.until
                found = True
    if not found:
        print(f"no check named '{args.name}' found", file=sys.stderr)
        return 1
    _save(data)
    print(f"acked '{args.name}' until {args.until}")
    return 0


def cmd_drain(args) -> int:
    """Called by the audit skill after running next_sweep checks. Moves them to history."""
    data = _load()
    drained = data["next_sweep"]
    for e in drained:
        e["ran_at"] = _now()
        data["history"].append(e)
    data["next_sweep"] = []
    data["history"] = data["history"][-200:]
    _save(data)
    print(f"drained {len(drained)} next_sweep checks to history")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="audit_add", description="Register audit checks for the audit skill"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="register a check")
    p_add.add_argument("mode", choices=["next", "forever"])
    p_add.add_argument("name")
    p_add.add_argument(
        "--kind", required=True, choices=["grep", "sql", "python", "shell"]
    )
    p_add.add_argument("--pattern", required=True)
    p_add.add_argument("--description", "--desc", default="")
    p_add.add_argument(
        "--severity", "--sev", default="med", choices=["high", "med", "low"]
    )
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="show registered checks")
    p_list.set_defaults(func=cmd_list)

    p_rm = sub.add_parser("rm", help="remove a check by name")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_rm)

    p_ack = sub.add_parser("ack", help="silence a check until a date")
    p_ack.add_argument("name")
    p_ack.add_argument("--until", required=True)
    p_ack.set_defaults(func=cmd_ack)

    p_drain = sub.add_parser(
        "drain", help="move next_sweep to history (called by audit skill)"
    )
    p_drain.set_defaults(func=cmd_drain)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
