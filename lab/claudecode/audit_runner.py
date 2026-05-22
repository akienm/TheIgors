#!/usr/bin/env python3
"""
audit_runner.py — T-audit-add-checks (#446)

Companion to audit_add.py. Loads audit_checks.json, runs each registered check
(forever + next_sweep), reports findings, and (optionally) drains next_sweep
to history when called with --drain-after.

Called by the audit skill as a new step after Step 17 (simplification review)
and before Step 18 (evaluate findings + fix).

Usage:
  audit_runner.py             # run all registered checks, print findings
  audit_runner.py --drain     # run + drain next_sweep entries to history afterward

Each finding is one line with severity prefix:
  [HIGH ] check_name: <details>
  [MED  ] check_name: <details>
  [LOW  ] check_name: <details>
  [PASS ] check_name: ok
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = Path(__file__).resolve().parent / "audit_checks.json"
DB_URL = os.environ["IGOR_HOME_DB_URL"]


def _load() -> dict:
    if not REGISTRY_PATH.exists():
        return {"next_sweep": [], "forever": [], "history": []}
    return json.loads(REGISTRY_PATH.read_text())


def _save(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n")


def _is_acked(entry: dict) -> bool:
    until = entry.get("ack_until")
    if not until:
        return False
    try:
        return datetime.fromisoformat(until) > datetime.now()
    except Exception:
        return False


def _format(entry: dict, status: str, detail: str) -> str:
    sev = (entry.get("severity") or "med").upper()
    return f"[{sev:<5}] {entry['name']}: {status}{(' — ' + detail) if detail else ''}"


def run_grep(entry: dict) -> tuple[str, str]:
    """Search for pattern in wild_igor/igor/. Reports if pattern found."""
    pattern = entry["pattern"]
    target = REPO_ROOT / "wild_igor" / "igor"
    if not target.exists():
        return "ERROR", f"target not found: {target}"
    try:
        result = subprocess.run(
            ["grep", "-rn", "-i", "--include=*.py", pattern, str(target)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "ERROR", "grep timed out"

    if result.returncode == 0 and result.stdout:
        lines = result.stdout.strip().splitlines()
        return "FAIL", f"{len(lines)} match(es) — first: {lines[0][:120]}"
    if result.returncode == 1:
        return "PASS", "no matches"
    return "ERROR", result.stderr.strip()[:200]


def run_sql(entry: dict) -> tuple[str, str]:
    """Run a SQL query against the home DB. Reports if any rows returned."""
    sql = entry["pattern"]
    try:
        import psycopg2
    except ImportError:
        return "ERROR", "psycopg2 not available"
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.close()
        if rows:
            return "FAIL", f"{len(rows)} row(s) — first: {str(rows[0])[:120]}"
        return "PASS", "no rows"
    except Exception as exc:
        return "ERROR", str(exc)[:200]


def run_shell(entry: dict) -> tuple[str, str]:
    """Run a shell one-liner. Exit code is authoritative: 0=PASS, non-0=FAIL."""
    try:
        result = subprocess.run(
            entry["pattern"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        return "ERROR", "shell timed out"
    if result.returncode == 0:
        detail = (
            result.stdout.strip().splitlines()[0][:120]
            if result.stdout.strip()
            else "ok"
        )
        return "PASS", detail
    detail = (
        (result.stdout or result.stderr).strip().splitlines()[0][:120]
        if (result.stdout or result.stderr).strip()
        else f"exit {result.returncode}"
    )
    return "FAIL", detail


def run_python(entry: dict) -> tuple[str, str]:
    """Run an inline Python expression. Truthy result = FAIL."""
    try:
        ns: dict = {"__builtins__": __builtins__}
        result = eval(entry["pattern"], ns)
    except Exception as exc:
        return "ERROR", str(exc)[:200]
    if result:
        return "FAIL", str(result)[:120]
    return "PASS", "falsy"


_DISPATCH = {
    "grep": run_grep,
    "sql": run_sql,
    "shell": run_shell,
    "python": run_python,
}


def run_one(entry: dict) -> str:
    if _is_acked(entry):
        return _format(entry, "ACKED", f"until {entry['ack_until']}")
    fn = _DISPATCH.get(entry["kind"])
    if not fn:
        return _format(entry, "ERROR", f"unknown kind: {entry['kind']}")
    status, detail = fn(entry)
    return _format(entry, status, detail)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run registered audit checks")
    parser.add_argument(
        "--drain",
        action="store_true",
        help="drain next_sweep entries to history after running",
    )
    args = parser.parse_args()

    data = _load()
    forever = data.get("forever", [])
    next_sweep = data.get("next_sweep", [])

    if not forever and not next_sweep:
        print("(no registered checks)")
        return 0

    print(
        f"=== Registered audit checks: {len(forever)} forever, {len(next_sweep)} next_sweep ==="
    )
    print()

    fail_count = 0
    error_count = 0

    for entry in forever + next_sweep:
        line = run_one(entry)
        print(line)
        if ": FAIL" in line:
            fail_count += 1
        elif ": ERROR" in line:
            error_count += 1

    print()
    print(
        f"=== Summary: {fail_count} fail, {error_count} error, "
        f"{len(forever) + len(next_sweep) - fail_count - error_count} pass ==="
    )

    if args.drain and next_sweep:
        for e in next_sweep:
            e["ran_at"] = datetime.now().isoformat()
            data["history"].append(e)
        data["next_sweep"] = []
        data["history"] = data["history"][-200:]
        _save(data)
        print(f"\ndrained {len(next_sweep)} next_sweep check(s) to history")

    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
