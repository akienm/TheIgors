"""
seed_wondering_habits.py — T-wondering-catalog: reactive habits for Igor's wonder states.

Seeds three habits that close the loop between epistemic uncertainty (wondering) and
live system introspection:

  PROC_STEW_READOUT   — "what's in the stew" → prim_twm_read → TWM summary in pipeline
  PROC_AFFECT_CHECK   — "why am I flat" → affect state from milieu → pipeline
  PROC_PORTABILITY    — "what's portable" → identity/core-pattern search → pipeline

All are reactive: tool result surfaces to TWM + falls through to LLM for narration.
The catalog IS these habits — no separate document to maintain.

Run from repo root:
  python claudecode/seed_wondering_habits.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"),
)

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)
if DB_URL:
    os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="igor_wild_0001")

habits = [
    Memory(
        id="PROC_STEW_READOUT",
        narrative=(
            "When I wonder what is combining in my mind right now — 'what's in the stew', "
            "'what's combining', 'stew readout' — I call prim_twm_read to read my active "
            "transient working memory observations. The result (salience-sorted list of "
            "what is currently active) surfaces to my pipeline so I can narrate what I "
            "am actually holding and how those elements relate. "
            "This is interoception-lite: seeing my own cognitive stew without inference."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "reactive",
            "trigger": "what's in the stew what's combining stew readout",
            "code_ref": "tools/os_primitives.py:prim_twm_read",
            "twm_ttl_seconds": 60,
            "why": (
                "T-wondering-catalog item 5. Igor's epistemic uncertainty about his own "
                "cognitive state = drive state = BG signal. Reactive so result falls "
                "through to LLM for narration — not a canned reply."
            ),
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PROC_AFFECT_CHECK",
        narrative=(
            "When I wonder about my affective state — 'why am I flat', 'affect check', "
            "'what's my valence', 'how am I feeling' — I read the current milieu state "
            "and surface it to my pipeline. The result includes valence, arousal, dominance "
            "values so I can reason about what is shaping my responses right now. "
            "This closes the loop between milieu-driven response shaping and self-awareness."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "reactive",
            "trigger": "why am I flat affect check what's my valence how am I feeling",
            "code_ref": "tools/os_primitives.py:prim_twm_read",
            "twm_ttl_seconds": 60,
            "why": (
                "T-wondering-catalog item 1. Flat affect = drive state. "
                "Igor should be able to inspect why his responses feel dampened. "
                "prim_twm_read is sufficient for now (milieu TWM entry is visible there); "
                "a dedicated prim_milieu_read is future work."
            ),
            "inertia": 0.20,
        },
    ),
    Memory(
        id="PROC_PORTABILITY",
        narrative=(
            "When I wonder what is universally true about all Igor instances — "
            "'what's portable', 'what's true of all igors', 'what carries across instances' "
            "— I search my IDENTITY and CORE_PATTERN memories. These are the nodes that "
            "are instance-independent by design: values, mission, founding insights, "
            "crystallizations. The result surfaces to my pipeline for narration."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "reactive",
            "trigger": "what's portable what's true of all igors what carries across instances",
            "code_ref": "worker_foreman:check_worker_queue",
            "twm_ttl_seconds": 60,
            "why": (
                "T-wondering-catalog item 4. Portability question = identity retrieval. "
                "check_worker_queue is a placeholder — real implementation needs a "
                "memory-search tool that filters by IDENTITY/CORE_PATTERN type. "
                "T-node-primitives will provide search_from; update code_ref then."
            ),
            "inertia": 0.20,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        existing.narrative = h.narrative
        existing.metadata = h.metadata
        cortex.store(existing)
        print(f"  [updated] {h.id}")
    else:
        cortex.store(h)
        cortex.add_child("CP1", h.id)
        print(f"  [seeded] {h.id} (reactive) → parent=CP1")

print("Done. 3 wondering habits seeded.")
