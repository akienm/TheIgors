#!/usr/bin/env python3
"""
seed_watchlist.py — GH-299 + T-versioned-seed-config.

Reads the watchlist spec from lab/seed/watchlist.yaml (source-of-truth, git-versioned)
and upserts it into the memories table as PROCEDURAL watch habits. Idempotent —
safe to re-run. The YAML file is the authority; this script is a projection
into the runtime cache (DB).

If the YAML file is missing, falls back to the embedded 2026-04-18 snapshot
so seed still works from a minimal checkout. The embedded copy is for recovery
only; normal edits should go through the YAML.

Restore command: python3 lab/claudecode/seed_watchlist.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Repo boot
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "wild_igor"))

from igor.memory.cortex import Cortex
from igor.memory.models import Memory, MemoryType

_SEED_YAML = _REPO / "lab" / "seed" / "watchlist.yaml"


# ── Fallback snapshot (2026-04-18 Akien dictation) ─────────────────────────
# Used only if the YAML is missing. Keep in sync with lab/seed/watchlist.yaml.

_FALLBACK_SPEC: dict[str, list[dict]] = {
    "questions": [
        {"id": "WATCH_Q_00", "text": "What does it mean to me?", "parent_cp": "CP4"},
        {"id": "WATCH_Q_01", "text": "What does that mean?", "parent_cp": "CP4"},
        {
            "id": "WATCH_Q_02",
            "text": "How must that work? How would that have to work?",
            "parent_cp": "CP4",
        },
        {
            "id": "WATCH_Q_03",
            "text": "Which choice is most in alignment with who I'd most like to be?",
            "parent_cp": "CP4",
        },
        {
            "id": "WATCH_Q_04",
            "text": "What's the first thing I say in response to that?",
            "parent_cp": "CP4",
        },
        {
            "id": "WATCH_Q_05",
            "text": "What looks like it would fit there?",
            "parent_cp": "CP4",
        },
        {
            "id": "WATCH_Q_06",
            "text": "How could we get around that?",
            "parent_cp": "CP4",
        },
        {"id": "WATCH_Q_07", "text": "Where is the lever?", "parent_cp": "CP4"},
        {
            "id": "WATCH_Q_08",
            "text": "How will us monkeys screw that up such that I get support questions?",
            "parent_cp": "CP4",
        },
    ],
    "topics": [
        {"id": "WATCH_T_00", "text": "Language", "parent_cp": "CP3"},
        {"id": "WATCH_T_01", "text": "Neurological systems", "parent_cp": "CP3"},
        {"id": "WATCH_T_02", "text": "Programming", "parent_cp": "CP3"},
        {"id": "WATCH_T_03", "text": "Igor's Design", "parent_cp": "CP3"},
        {"id": "WATCH_T_04", "text": "AI", "parent_cp": "CP3"},
        {"id": "WATCH_T_05", "text": "Claude Code", "parent_cp": "CP3"},
        {"id": "WATCH_T_06", "text": "Biology", "parent_cp": "CP3"},
        {"id": "WATCH_T_07", "text": "Psychology", "parent_cp": "CP3"},
        {"id": "WATCH_T_08", "text": "Culture and sociology", "parent_cp": "CP3"},
    ],
}


def _load_spec() -> tuple[dict[str, list[dict]], str]:
    """Load the watchlist spec. Returns (spec, source_label)."""
    if _SEED_YAML.exists():
        import yaml

        spec = yaml.safe_load(_SEED_YAML.read_text())
        return spec, f"yaml:{_SEED_YAML.name}"
    return _FALLBACK_SPEC, "fallback:embedded_2026_04_18"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_watchlist(cortex: Cortex) -> dict[str, Any]:
    """Upsert the full watchlist. Returns a small report."""
    spec, source_label = _load_spec()
    now = _now_iso()
    counts = {"questions": 0, "topics": 0}

    for q in spec.get("questions", []):
        mem = Memory(
            id=q["id"],
            narrative=q["text"],
            memory_type=MemoryType.PROCEDURAL,
            parent_id=q.get("parent_cp", "CP4"),
            valence=0.6,
            metadata={
                "habit_type": "watch",
                "watch_type": "question",
                "watch_label": q["text"],
                "trigger": q["text"].lower(),
                "deposited_by": "seed_watchlist",
                "deposited_at": now,
                "source": source_label,
                "priority": "high",
            },
        )
        cortex.store(mem)
        counts["questions"] += 1

    for t in spec.get("topics", []):
        mem = Memory(
            id=t["id"],
            narrative=t["text"],
            memory_type=MemoryType.PROCEDURAL,
            parent_id=t.get("parent_cp", "CP3"),
            valence=0.6,
            metadata={
                "habit_type": "watch",
                "watch_type": "topic",
                "watch_label": t["text"],
                "trigger": t["text"].lower(),
                "deposited_by": "seed_watchlist",
                "deposited_at": now,
                "source": source_label,
                "priority": "high",
            },
        )
        cortex.store(mem)
        counts["topics"] += 1

    counts["source"] = source_label
    return counts


def main():
    import os

    db_url = os.environ["IGOR_HOME_DB_URL"]

    db_path = Path(
        os.path.expanduser(
            os.environ.get("IGOR_DB_PATH", "~/.TheIgors/Igor-wild-0001/wild-0001.db")
        )
    )
    cortex = Cortex()

    report = seed_watchlist(cortex)
    print(
        f"seed_watchlist: questions={report['questions']} topics={report['topics']} "
        f"total={report['questions'] + report['topics']} source={report['source']}"
    )


if __name__ == "__main__":
    main()
