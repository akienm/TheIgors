#!/usr/bin/env python3
"""
seed_tiered_research_habit.py — T-tiered-research-habit.

Seeds PROC_TIERED_RESEARCH: a PROCEDURAL action habit that fires on
research-shaped prompts ('research X', 'look up X', 'tell me about X')
and auto-dispatches to tools.tiered_research:research_and_deposit —
which in turn runs tiered_research (memory→web→local→cloud) AND
deposits the Q/A pair as a FACTUAL memory for future graph lookup.

This is the automation layer on top of T-tiered-research-tool. The tool
alone is read-only; this habit gives Igor the reflex to *use* it when
Akien asks for research, and captures the answer so it compounds.

Idempotent — safe to re-run. Upserts one memory at id=PROC_TIERED_RESEARCH.
Restore: `python3 lab/claudecode/seed_tiered_research_habit.py`
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "wild_igor"))

from igor.memory.cortex import Cortex
from igor.memory.models import Memory, MemoryType

_HABIT_ID = "PROC_TIERED_RESEARCH"

# Trigger phrases — use '|' pipe syntax so basal_ganglia's phrase-matcher
# treats each as an independent match target. Kept narrow: these are
# explicit research *requests*, not every "what" / "why" question.
_TRIGGER = (
    "research |look up |find out about |tell me about "
    "|what do you know about |what can you tell me about "
    "|dig into |background on |give me background on "
)

_NARRATIVE = (
    "When Akien asks me to research a topic — phrases like 'research X', "
    "'look up X', 'tell me about X', 'dig into X' — I run the tiered "
    "research pipeline (memory first, then web, then local LLM, then "
    "cloud LLM if needed) and deposit the Q/A pair into my memory as a "
    "FACTUAL node. The deposit means the next time the topic comes up "
    "I find it via graph search instead of re-spending on web/LLM tiers. "
    "Tool: research_and_deposit (code_ref: tools.tiered_research)."
)


def seed_tiered_research(cortex: Cortex) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    mem = Memory(
        id=_HABIT_ID,
        narrative=_NARRATIVE,
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP2",
        valence=0.5,
        metadata={
            "habit_type": "action",
            "code_ref": "tools.tiered_research:research_and_deposit",
            "trigger": _TRIGGER,
            "deposited_by": "seed_tiered_research_habit",
            "deposited_at": now,
            "source": "T-tiered-research-habit",
            "priority": "normal",
            "tags": ["research", "habit", "tiered_research"],
        },
    )
    cortex.store(mem)
    return {"id": _HABIT_ID, "triggers": _TRIGGER}


def main():
    db_url = os.getenv(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )
    os.environ["IGOR_HOME_DB_URL"] = db_url

    db_path = Path(
        os.path.expanduser(
            os.environ.get("IGOR_DB_PATH", "~/.TheIgors/Igor-wild-0001/wild-0001.db")
        )
    )
    cortex = Cortex()

    report = seed_tiered_research(cortex)
    print(f"seed_tiered_research_habit: upserted {report['id']}")


if __name__ == "__main__":
    main()
