#!/usr/bin/env python3
"""audit_immobile_tickets.py — T-audit-immobile-observe-tickets audit tool.

Sweep the current ticket queue for observe/wait/monitor-shaped tickets and
classify each as MOBILE (has a trip condition) or IMMOBILE (no clear next-move
trigger).

Trip-condition heuristics (match any → MOBILE):
- TTL / date language: "re-evaluate in", "after YYYY-MM-DD", "in N days"
- Count thresholds: "once N", "after N", "at least N"
- Event gates: "when X fires", "when X happens", gate: / gated on a sibling
- Companion ticket refs: "gated on T-", "blocks T-", "related_to" set
- Body-explicit next-move: "next move:", "trigger:", "when done", "success criteria"
- Explicit "no tests because:" or "observation only, next ticket files follow-up"

Observe-shape heuristic (match any → candidate):
- "observe", "wait for", "monitor", "run and see", "check back", "see if"
- "trip condition" mentioned (usually paired with an explicit condition)

Output: lab/design_docs/queue_hygiene/immobile_tickets_YYYY-MM-DD.md
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path

import psycopg2
import psycopg2.extras

DB_URL = os.getenv("IGOR_HOME_DB_URL")
if not DB_URL:
    print("IGOR_HOME_DB_URL is required", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parents[2]
REPORT = (
    REPO
    / "lab/design_docs/queue_hygiene"
    / f"immobile_tickets_{date.today().isoformat()}.md"
)

OBSERVE_PATTERNS = [
    r"\bobserve\b",
    r"\bwait for\b",
    r"\bmonitor\b",
    r"\brun and see\b",
    r"\bcheck back\b",
    r"\bsee if\b",
    r"\bmeasure (whether|if)\b",
]
TRIP_PATTERNS = [
    # TTL / date
    r"\bre-?evaluate\b",
    r"\bafter \d+",
    r"\bin \d+ (day|week|month)",
    r"\b20\d\d-\d\d-\d\d\b",
    # Count
    r"\bonce (at least )?\d+",
    r"\bafter (at least )?\d+",
    r"\bwhen N\b",
    r"\b\d+ (turn|close|trigger|fire|run)",
    # Event gate
    r"\bwhen [A-Z][A-Z_]+ fires?\b",
    r"\bwhen [A-Z][A-Z_]+ (happens?|triggers?)\b",
    r"\bgate:",
    r"\bgated on\b",
    # Explicit next-move
    r"\bnext[- ]move:",
    r"\btrigger:",
    r"\bsuccess criteri",
    r"\btrip condition\b",
    r"\btest[- ]?plan:",
    # Body-explicit self-annotations
    r"\bobservation only\b.*\bfollow-up\b",
]

OBSERVE_RE = re.compile("|".join(OBSERVE_PATTERNS), re.IGNORECASE)
TRIP_RE = re.compile("|".join(TRIP_PATTERNS), re.IGNORECASE)


def _count(pattern: re.Pattern, body: str) -> int:
    return sum(1 for _ in pattern.finditer(body)) if body else 0


def classify(body: str, related_to: str | None, gate: str | None) -> tuple[str, dict]:
    """Return (verdict, evidence). verdict: MOBILE | IMMOBILE | NOT_OBSERVE."""
    observe_n = _count(OBSERVE_RE, body)
    if not observe_n:
        return "NOT_OBSERVE", {}
    trip_n = _count(TRIP_RE, body)
    evidence = {
        "observe_hits": observe_n,
        "trip_hits": trip_n,
        "gate": gate,
        "related_to": related_to,
    }
    if trip_n or gate or related_to:
        return "MOBILE", evidence
    return "IMMOBILE", evidence


def main() -> int:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SET search_path TO clan, public")
    cur.execute("""
        SELECT id, narrative, metadata
        FROM memories
        WHERE parent_id = 'TICKETS_ROOT'
          AND metadata->>'status' IN ('pending', 'blocked', 'in_progress', 'awaiting_approval')
        """)
    rows = cur.fetchall()
    conn.close()

    observe_candidates = 0
    immobile = []
    mobile = []
    for row in rows:
        body = row["narrative"] or ""
        meta = row["metadata"] or {}
        related = meta.get("related_to")
        gate = meta.get("gate")
        verdict, evidence = classify(body, related, gate)
        if verdict == "NOT_OBSERVE":
            continue
        observe_candidates += 1
        entry = {
            "id": row["id"],
            "status": meta.get("status"),
            "evidence": evidence,
            "body_snippet": (body[:200] + "…") if len(body) > 200 else body,
        }
        if verdict == "MOBILE":
            mobile.append(entry)
        else:
            immobile.append(entry)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Immobile-ticket audit — {date.today().isoformat()}",
        "",
        f"Scanned {len(rows)} pending/blocked/in_progress/awaiting_approval tickets.",
        f"Observe-shape candidates: {observe_candidates}",
        f"- MOBILE (has trip condition): {len(mobile)}",
        f"- IMMOBILE (needs trip condition or close): {len(immobile)}",
        "",
        "## Immobile tickets (action required)",
        "",
    ]
    if not immobile:
        lines.append("_None — every observe-shape ticket carries a trip condition._")
    else:
        for e in immobile:
            lines.append(f"### {e['id']} [{e['status']}]")
            lines.append("")
            ev = e["evidence"]
            lines.append(
                f"Observe hits: {ev['observe_hits']} / trip hits: {ev['trip_hits']} / gate: {ev['gate']} / related: {ev['related_to']}"
            )
            lines.append("")
            lines.append("```")
            lines.append(e["body_snippet"])
            lines.append("```")
            lines.append("")
            lines.append(
                "Action: add a trip condition (TTL / count / event / companion / body-explicit) or close with reason."
            )
            lines.append("")

    lines.extend(["", "## Mobile tickets (reference only)", ""])
    for e in mobile:
        ev = e["evidence"]
        lines.append(
            f"- `{e['id']}` [{e['status']}] — observe={ev['observe_hits']} trip={ev['trip_hits']} gate={ev['gate']} related={ev['related_to']}"
        )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")
    print(f"observe candidates: {observe_candidates} / immobile: {len(immobile)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
