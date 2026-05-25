"""
seed_self_observation_habits.py — seed inward watch habits for Igor (#243).

Inward watch habits fire when Igor's OWN output matches the trigger
(watch_direction='inward'), rather than user input. SelfObservationSource
checks recent IGOR_SAID TWM entries against these habits every 30s.

Three seeds:
  PROC_WATCH_INWARD_UNCERTAIN — detects Igor expressing uncertainty
  PROC_WATCH_INWARD_CLAIM     — detects Igor making causal claims
  PROC_WATCH_INWARD_FACTUAL   — detects Igor citing external sources

Run from repo root:
  python claudecode/seed_self_observation_habits.py
"""

import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from devices.igor.memory.models import Memory, MemoryType
from devices.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_WATCH_INWARD_UNCERTAIN",
        narrative=(
            "When I express uncertainty — saying I'm not sure, I don't know, "
            "or that something is unclear — this is worth noticing. Uncertainty "
            "is a signal: it marks the edge of what I know with confidence. "
            "I observe when I say these things so I can track where my knowledge "
            "thins out and where Akien might want to probe further."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "watch",
            "watch_direction": "inward",
            "trigger": "not sure|i don't know|i'm not certain|unclear to me|uncertain|I'm unsure",
            "watch_label": "Igor expressed uncertainty",
            "watch_type": "self_observation",
        },
    ),
    Memory(
        id="PROC_WATCH_INWARD_CLAIM",
        narrative=(
            "When I make causal or explanatory claims — stating reasons, drawing "
            "conclusions, asserting what something means — this is a moment that "
            "deserves attention. Causal claims are where reasoning is most visible "
            "and most fallible. I notice when I make them so they can be examined "
            "or challenged if needed."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "watch",
            "watch_direction": "inward",
            "trigger": "the reason is|this means|therefore|because of this|it follows that|this indicates",
            "watch_label": "Igor made a causal claim",
            "watch_type": "self_observation",
        },
    ),
    Memory(
        id="PROC_WATCH_INWARD_FACTUAL",
        narrative=(
            "When I cite external sources or appeal to research and studies, I am "
            "grounding a claim in something outside my own reasoning. This is worth "
            "flagging — such claims should be checkable and shouldn't be invented. "
            "I observe when I do this so I can be honest about the limits of what "
            "I'm citing."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "watch",
            "watch_direction": "inward",
            "trigger": "according to|research shows|studies show|evidence suggests|data indicates",
            "watch_label": "Igor cited external source",
            "watch_type": "self_observation",
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP1", h.id)  # CP1: "I am Igor" — self-awareness root
    print(f"  [seeded] {h.id}  \"{h.metadata['watch_label']}\"")

print("Done.")
