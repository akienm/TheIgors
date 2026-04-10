#!/usr/bin/env python3
"""
decision_manager.py — Record a design decision atomically.

Does three things in one shot:
  1. Prepends the decision line to decisions_log.dsb (file stays canonical)
  2. Updates the DSB header (latest=Dxx, updated=date)
  3. Upserts to docs_entries Postgres table (token-efficient DB mirror)
  4. Posts to cc_queue for Igor memory flush (non-fatal if Igor down)

Usage:
    python3 claudecode/decision_manager.py add D133 "session-in-db" "implemented" \
        "sessions table in Postgres; session_manager.py; sessions.md rendered from DB"
    python3 claudecode/decision_manager.py show [N]     — last N decisions from DB
    python3 claudecode/decision_manager.py get D133     — print one decision

Called by /decided skill at Step 2 to eliminate manual DSB editing.

Ref: D133, T-decided-habit
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DSB_FILE = Path.home() / "TheIgors" / "design_docs_for_igor" / "decisions_log.dsb"
DB_URL = os.getenv("IGOR_HOME_DB_URL") or os.getenv("IGOR_DB_URL")


# ── DB helpers ────────────────────────────────────────────────────────────────


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _upsert_docs_entry(decision_id: str, line: str):
    """Upsert decision line into docs_entries."""
    if not DB_URL:
        return
    try:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        with _conn() as conn:
            with conn.cursor() as c:
                c.execute(
                    """
                    INSERT INTO docs_entries (source, entry_key, entry_type, content, synced_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (source, entry_key) DO UPDATE SET
                        entry_type = EXCLUDED.entry_type,
                        content    = EXCLUDED.content,
                        synced_at  = EXCLUDED.synced_at
                """,
                    ("decisions_log", decision_id, "decision", line, now),
                )
            conn.commit()
    except Exception as e:
        print(f"  [warn] docs_entries upsert failed: {e}", file=sys.stderr)


def _flush_to_igor(decision_id: str, description: str):
    """Post to cc_queue for Igor memory flush. Non-fatal."""
    try:
        subprocess.run(
            [
                sys.executable,
                str(Path.home() / "TheIgors" / "claudecode" / "cc_queue.py"),
                "flush_decision",
                decision_id,
                description,
            ],
            timeout=10,
            capture_output=True,
        )
    except Exception:
        pass  # Igor down is fine — DSB + DB are durable


# ── DSB helpers ───────────────────────────────────────────────────────────────


def _update_dsb(
    decision_id: str, short_name: str, status: str, description: str
) -> str:
    """Prepend decision line to DSB. Update header. Return the line."""
    line = f"{decision_id}|{short_name}|{status}|{description}"
    today = datetime.now().strftime("%Y-%m-%d")

    text = DSB_FILE.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Update header: latest= and updated=
    new_lines = []
    header_done = False
    decision_inserted = False

    last_decision_idx = -1
    for i, l in enumerate(lines):
        if re.match(r"^D\d+\|", l):
            last_decision_idx = i

    for i, l in enumerate(lines):
        # Update DOC header line
        if l.startswith("DOC|") and not header_done:
            l = re.sub(r"updated=\S+", f"updated={today}", l)
            l = re.sub(r"latest=\S+", f"latest={decision_id}", l)
            new_lines.append(l)
            header_done = True
            continue

        new_lines.append(l)

        # Insert after the last existing Dxxx| line (append convention — oldest-first)
        if i == last_decision_idx and not decision_inserted:
            new_lines.append(line)
            decision_inserted = True

    if not decision_inserted:
        # No existing decisions — append at end
        new_lines.append(line)

    DSB_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return line


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_add(args: list[str]):
    """Add a decision: add <id> <short_name> <status> <description>"""
    if len(args) < 4:
        print(
            'Usage: decision_manager.py add <id> <short_name> <status> "<description>"'
        )
        print("  status values: implemented | defined | planned | implemented-poc")
        sys.exit(2)

    decision_id = args[0].upper()
    short_name = args[1]
    status = args[2]
    description = args[3]

    # 1. Update DSB file
    line = _update_dsb(decision_id, short_name, status, description)
    print(f"DSB updated: {line}")

    # 2. Upsert to docs_entries
    if DB_URL:
        _upsert_docs_entry(decision_id, line)
        print(f"docs_entries upserted: {decision_id}")
    else:
        print("  [skip] IGOR_HOME_DB_URL not set — DB upsert skipped")

    # 3. Flush to Igor memory (best-effort)
    _flush_to_igor(decision_id, description)
    print(f"Igor flush queued: {decision_id}")


def cmd_show(n: int = 10):
    """Show last N decisions from DB (or DSB if no DB)."""
    if DB_URL:
        try:
            with _conn() as conn:
                with conn.cursor() as c:
                    c.execute(
                        """
                        SELECT content FROM docs_entries
                        WHERE source='decisions_log' AND entry_type='decision'
                        ORDER BY entry_key DESC LIMIT %s
                    """,
                        (n,),
                    )
                    rows = c.fetchall()
            print(f"Last {n} decisions (from DB):")
            for r in rows:
                print(f"  {r['content']}")
            return
        except Exception:
            pass

    # Fallback: read DSB directly
    text = DSB_FILE.read_text(encoding="utf-8", errors="replace")
    decisions = [l for l in text.splitlines() if re.match(r"^D\d+\|", l)]
    print(f"Last {n} decisions (from DSB):")
    for l in decisions[:n]:
        print(f"  {l}")


def cmd_get(decision_id: str):
    """Print one decision by ID."""
    decision_id = decision_id.upper()
    if DB_URL:
        try:
            with _conn() as conn:
                with conn.cursor() as c:
                    c.execute(
                        "SELECT content FROM docs_entries WHERE source='decisions_log' AND entry_key=%s",
                        (decision_id,),
                    )
                    r = c.fetchone()
            if r:
                print(r["content"])
                return
        except Exception:
            pass

    # Fallback: grep DSB
    text = DSB_FILE.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith(f"{decision_id}|"):
            print(line)
            return
    print(f"Decision {decision_id} not found")
    sys.exit(1)


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"

    if cmd == "add":
        cmd_add(sys.argv[2:])
    elif cmd == "show":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        cmd_show(n)
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: decision_manager.py get <id>")
            sys.exit(2)
        cmd_get(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}  (add|show|get)")
        sys.exit(2)


if __name__ == "__main__":
    main()
