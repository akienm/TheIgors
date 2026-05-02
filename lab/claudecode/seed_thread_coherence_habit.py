"""
seed_thread_coherence_habit.py — Thread coherence self-monitoring habit.

Seeds PROC_THREAD_DRIFT: fires when ThreadCoherenceSource detects topic drift
(THREAD_COHERENCE|drift=yes in TWM). Prompts Igor to observe the shift and
recalibrate attention.

Run from repo root:
  python claudecode/seed_thread_coherence_habit.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="Igor-wild-0001")


def seed(habit: Memory, parent: str = "CP1") -> None:
    existing = cortex.get(habit.id)
    if existing:
        existing.narrative = habit.narrative
        existing.metadata = habit.metadata
        cortex.store(existing)
        print(f"  [updated] {habit.id}")
    else:
        cortex.store(habit)
        cortex.add_child(parent, habit.id)
        print(f"  [seeded]  {habit.id} → parent={parent}")


print("Seeding thread coherence habit...")

seed(
    Memory(
        id="PROC_THREAD_DRIFT",
        narrative=(
            "When my working memory contains THREAD_COHERENCE|drift=yes, it means my recent "
            "turns shifted topic significantly from the previous turn — the activated node overlap "
            "dropped below the drift threshold. This is my self-monitoring signal for conversational "
            "coherence, analogous to noticing I've drifted in thought.\n\n"
            "When this fires, I should:\n"
            "1. Internally register the topic shift — acknowledge it as a signal, not a failure.\n"
            "2. If I'm mid-task and the shift is unexpected, briefly reconnect to the thread "
            "('I notice we've shifted from X — should I continue with X or stay on the new topic?').\n"
            "3. If the shift was intentional (user introduced a new request), no correction needed — "
            "just maintain awareness that context has changed.\n"
            "4. Don't narrate this process to the user unless reconnecting. Keep it internal.\n\n"
            "This habit is part of D233 spreading activation — thread coherence score measures "
            "how well my cognition is maintaining context across turns. Low score = the activated "
            "node sets are diverging, which is a real cognitive signal worth attending to."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        valence=0.5,
        metadata={
            "habit_type": "cognitive",
            "conditions": {
                "keywords": [
                    "THREAD_COHERENCE",
                    "drift=yes",
                    "thread drift",
                    "topic shift",
                ],
            },
            "match_mode": "conditions_first",
            "inertia": 0.20,
            "provenance": "seed:T-thread-coherence",
            "why": (
                "ThreadCoherenceSource fires THREAD_COHERENCE|drift=yes when bg_scoring.top "
                "overlap between consecutive turns drops below 0.15. Same as how a person "
                "notices they've drifted in conversation — the signal triggers self-observation "
                "not action. Low salience (0.55) so it's a background signal, not an alarm."
            ),
        },
    ),
)

print("Done.")
