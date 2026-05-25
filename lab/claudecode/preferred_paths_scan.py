"""
preferred_paths_scan.py — Scan git history for deprecated-form fallback patterns.

Looks at ~60 days of commits for places where Sonnet wrote a deprecated form
(raw psql, channel.py direct write, print(), etc.) when a preferred form
existed. Candidates that appear ≥3 times are surfaced for review.

Output is a candidate list — never auto-files palace nodes.
Akien reviews and decides which to merge into theigors/rules/preferred_paths/.

Updated 2026-04-29T00:00:00Z
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Pattern


@dataclass
class PathScanReport:
    """Collects and summarizes deprecated-form hits from git history."""

    since_days: int = 60
    min_occurrences: int = 3
    _candidates: dict[str, list[dict]] = field(default_factory=dict)

    # Patterns: (pattern_name, deprecated_regex, preferred_description)
    PATTERNS: list[tuple[str, str, str]] = field(
        default_factory=lambda: [
            (
                "raw-psql-in-code",
                r"psycopg2\.connect\(",
                "memory_get() / memory_search() MCP tools for palace reads",
            ),
            (
                "channel-direct-write",
                r"from lab\.claudecode\.channel import|channel\.send\(",
                "IMAP bus or _post_to_channel() wrapper",
            ),
            (
                "print-in-igor",
                r"^\+\s+print\(",
                "self.log.info / self.log.warning (IgorBase logger)",
            ),
            (
                "new-memory-type",
                r"MemoryType\.\w+ = |class MemoryType.*Enum",
                "metadata tag on existing MemoryType",
            ),
            (
                "new-feature-flag",
                r"IGOR_\w+_ENABLED\s*=\s*['\"]?false",
                "build to intent + go-live-when companion ticket",
            ),
            (
                "direct-db-write",
                r"cursor\(\)\.execute\(['\"]INSERT|cursor\(\)\.execute\(['\"]UPDATE",
                "PGDatabaseProxy / cortex.store()",
            ),
        ]
    )

    def _run_git(self, cmd: str) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            return result.stdout
        except Exception as e:
            return f"[ERROR] {e}"

    def scan(self) -> dict[str, list[dict]]:
        """
        Scan git log from the last since_days days for deprecated-form hits.
        Returns {pattern_name: [{commit, file, line, context}]} for hits with
        ≥ min_occurrences.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=self.since_days)).strftime(
            "%Y-%m-%d"
        )
        raw_hits: dict[str, list[dict]] = {p[0]: [] for p in self.PATTERNS}

        # Get patch content from git log
        diff_output = self._run_git(
            f"git log --since={since} --patch --unified=0 "
            f"-- 'lab/**/*.py' 2>/dev/null"
        )

        current_commit = ""
        current_file = ""
        for line in diff_output.splitlines():
            if line.startswith("commit "):
                current_commit = line.split()[1][:12]
            elif line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("+") and not line.startswith("+++"):
                added_line = line[1:]
                for name, pattern, _ in self.PATTERNS:
                    if re.search(pattern, added_line):
                        raw_hits[name].append(
                            {
                                "commit": current_commit,
                                "file": current_file,
                                "line": added_line.strip()[:120],
                            }
                        )

        # Filter to candidates with ≥ min_occurrences
        self._candidates = {
            name: hits
            for name, hits in raw_hits.items()
            if len(hits) >= self.min_occurrences
        }
        return self._candidates

    def render(self) -> str:
        if not self._candidates:
            return "No candidates found (all patterns < 3 occurrences)."

        lines = [
            f"preferred_paths scan — last {self.since_days} days",
            f"Threshold: ≥{self.min_occurrences} occurrences",
            f"Candidates: {len(self._candidates)}",
            "",
        ]
        for name, hits in sorted(self._candidates.items(), key=lambda x: -len(x[1])):
            pattern_meta = next((p for p in self.PATTERNS if p[0] == name), None)
            preferred = pattern_meta[2] if pattern_meta else "?"
            lines.append(f"### {name} ({len(hits)} hits)")
            lines.append(f"  Preferred form: {preferred}")
            lines.append(f"  Sample hits:")
            for h in hits[:3]:
                lines.append(f"    [{h['commit']}] {h['file']}: {h['line'][:80]}")
            lines.append("")

        lines.append(
            "Review candidates — merge approved ones into theigors/rules/preferred_paths/."
        )
        return "\n".join(lines)

    def to_palace_drafts(self) -> list[dict]:
        """
        Return palace node draft dicts for each candidate.
        These are NOT inserted — Akien reviews and decides which to add.
        """
        drafts = []
        for name, hits in self._candidates.items():
            pattern_meta = next((p for p in self.PATTERNS if p[0] == name), None)
            if not pattern_meta:
                continue
            _, deprecated_regex, preferred = pattern_meta
            drafts.append(
                {
                    "path": f"theigors/rules/preferred_paths/{name}",
                    "title": f"{name} (auto-candidate)",
                    "content": (
                        f"applies_when: plan or diff adds pattern matching: {deprecated_regex}\n"
                        f"deprecated: {name}\n"
                        f"preferred: {preferred}\n"
                        f"why: auto-detected from {len(hits)} occurrences in last 60 days\n"
                        f"status: CANDIDATE — review before promoting to palace"
                    ),
                    "hit_count": len(hits),
                }
            )
        return drafts


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan git history for preferred_paths candidates"
    )
    parser.add_argument("--since-days", type=int, default=60)
    parser.add_argument("--min-occurrences", type=int, default=3)
    parser.add_argument("--output", default=None, help="Write candidates JSON to file")
    args = parser.parse_args()

    report = PathScanReport(
        since_days=args.since_days, min_occurrences=args.min_occurrences
    )
    report.scan()
    print(report.render())

    if args.output:
        import json

        drafts = report.to_palace_drafts()
        with open(args.output, "w") as f:
            json.dump(drafts, f, indent=2)
        print(f"\nDrafts written to {args.output}")


if __name__ == "__main__":
    main()
