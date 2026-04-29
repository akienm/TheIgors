"""
scan_for_rest_drafter.py — Auto-draft a scan-for-rest ticket when audit-day
finds a fix-one-leave-many signature change.

When a function signature changes in N callers but M others still use the old
form, this tool drafts a 'T-scan-for-remaining-call-sites-<area>' ticket to
/tmp/. The ticket is never auto-filed — it surfaces in the next /decided
session for Akien's review.

Called by audit-day's fix-one-leave-many sweep handler.

Updated 2026-04-29T00:00:00Z
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class ScanForRestDrafter:
    """Drafts a ticket capturing partial call-graph signature changes."""

    def draft(
        self,
        function_name: str,
        found_callers: list[str],
        missing_callers: list[str],
        change_description: str = "",
        output_path: Path | None = None,
    ) -> dict:
        """
        Draft a ticket for the remaining call sites that weren't updated.
        Returns the ticket dict (also written to /tmp/ if output_path not given).
        """
        area = self._detect_area(missing_callers + found_callers)
        ticket_id = f"T-scan-remaining-{function_name[:20]}-{area}"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        found_str = "\n".join(f"  - {f}" for f in found_callers)
        missing_str = "\n".join(f"  - {f}" for f in missing_callers)

        description = f"""\
Fix-one-leave-many: `{function_name}` signature changed in {len(found_callers)} caller(s) but {len(missing_callers)} caller(s) still use the old form.

{change_description}

Updated callers:
{found_str or '  (none provided)'}

Callers still on old signature:
{missing_str or '  (none provided)'}

**Affected files:** {', '.join(missing_callers[:5]) or 'TBD — discovery step in sprint'}
**Design rules:** docs-in-code (update docstrings alongside signature changes); oop-first if callers are class methods.
**Scope boundary:** IN: update {function_name} call sites in the listed files. OUT: functional changes to those callers.
**Test plan:** run full test suite after each file updated; fix failures before next file.

Auto-drafted by scan_for_rest_drafter.py at {now}. Review before filing.
"""

        ticket = {
            "id": ticket_id,
            "title": f"scan remaining call sites — {function_name}",
            "size": "S" if len(missing_callers) <= 3 else "M",
            "status": "pending",
            "tags": ["scan-for-rest", area],
            "description": description,
            "decision_id": "",
            "gate": None,
            "priority": 0.6,
            "worker": "claude",
            "created_at": now,
            "draft": True,
        }

        out = output_path or Path("/tmp") / f"scan-for-rest-{function_name[:20]}.json"
        out.write_text(json.dumps(ticket, indent=2))
        return ticket

    def _detect_area(self, files: list[str]) -> str:
        for f in files:
            if "brainstem" in f:
                return "brainstem"
            if "cognition/reasoners" in f:
                return "reasoning"
            if "cognition" in f:
                return "cognition"
            if "memory" in f:
                return "memory"
            if "network" in f:
                return "network"
            if "tools" in f:
                return "tools"
        return "misc"


def main():
    parser = argparse.ArgumentParser(description="Draft a scan-for-rest ticket")
    parser.add_argument("--function", required=True, help="Changed function name")
    parser.add_argument("--found-callers", default="", help="Comma-separated updated callers")
    parser.add_argument("--missing-callers", default="", help="Comma-separated stale callers")
    parser.add_argument("--description", default="", help="Brief change description")
    parser.add_argument("--output", default=None, help="Output JSON path (default: /tmp/)")
    args = parser.parse_args()

    drafter = ScanForRestDrafter()
    ticket = drafter.draft(
        function_name=args.function,
        found_callers=[f for f in args.found_callers.split(",") if f],
        missing_callers=[f for f in args.missing_callers.split(",") if f],
        change_description=args.description,
        output_path=Path(args.output) if args.output else None,
    )
    out_path = args.output or f"/tmp/scan-for-rest-{args.function[:20]}.json"
    print(f"Drafted ticket {ticket['id']} → {out_path}")
    print(f"  Missing callers: {len([f for f in args.missing_callers.split(',') if f])}")
    print(f"  Review before filing: /decided will pick this up from /tmp/")


if __name__ == "__main__":
    main()
