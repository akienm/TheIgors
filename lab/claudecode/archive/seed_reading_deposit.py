#!/usr/bin/env python3
"""
Seed PROC_READING_DEPOSIT — reading session behavioral directive.
During reading, Igor's job is to deposit nodes into the matrix, not reason or perform.
"""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "wild_igor"))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors/Igor-wild-0001/wild-0001.db"))

from igor.memory.cortex import Cortex
from igor.memory.models import Memory, MemoryType

db_path = os.environ["IGOR_DB_PATH"]
cortex = Cortex(Path(db_path))

habit = Memory(
    id="PROC_READING_DEPOSIT",
    narrative=(
        "During a reading session my job is to deposit nodes into the matrix, not to reason or perform. "
        "Read the chunk → G54 extracts it → move to the next chunk. "
        "Do not escalate to cloud to 'think about' what I just read — "
        "the matrix is the thinker; LLMs are graph trainers. "
        "Only use cloud if Akien asks a specific question that requires reasoning "
        "from what has already been deposited."
    ),
    memory_type=MemoryType.PROCEDURAL,
    source="seed",
    confidence=0.95,
    context_of_encoding="seeded|reading_session_directive|2026-03-11",
    metadata={
        "trigger": "reading book chapter damasio read_chunk open_book",
        "response_template": "deposit",
        "context": "reading_session",
        "activation_contexts": ["reading", "book", "chapter", "read_chunk"],
    },
)
cortex.store(habit)
cortex.add_child("CP4", habit.id)   # make everything suck less — efficient ingestion
cortex.add_child("CP3", habit.id)   # there's always a why — follow the causal chain, build it

# Also add an interpretive edge: reading context → this directive fires
try:
    cortex.add_interpretive_edge(
        from_id="CP4",
        to_id="PROC_READING_DEPOSIT",
        direction="activation",
        condition_csb="context=reading_session",
        meaning_payload=(
            "Reading is investment in the matrix, not performance. "
            "Every chunk deposited is a future LLM call the graph handles instead."
        ),
        action_pointer="read_chunk → G54 → next_chunk",
    )
    print("Interpretive edge CP4 → PROC_READING_DEPOSIT added")
except Exception as e:
    print(f"Edge note: {e}")

print(f"\nStored: {habit.id}")
print(f"Narrative: {habit.narrative[:80]}...")
