"""
seed_foreground_reading_habits.py — D107 foreground reading habits.

Seeds three habits:
  PROC_READ_NOW         — "read this / read this slowly / <URL> / <file path>"
                          → start_foreground_reading()
  PROC_STOP_READING     — "stop reading / stop background reading / pause reading"
                          → stop_foreground_reading() → "One moment please…"
  PROC_QUEUE_FOR_INGEST — "queue this for ingestion / queue this for reading / add to read list"
                          → existing book_learner queue path (no change to that flow)

Run from repo root:
  python claudecode/seed_foreground_reading_habits.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_READ_NOW",
        narrative=(
            "When Akien sends me a URL, a file path, or says 'read this' or 'read this slowly', "
            "I start reading it sentence-by-sentence in the foreground web UI. "
            "I call start_foreground_reading() with the URL or path as input_text. "
            "One sentence appears every second so Akien can follow along. "
            "I do NOT add it to the background learn queue — this is a live foreground read. "
            "If Akien says 'queue this for reading' instead, I use the queue path."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": (
                "read this read this slowly read now read aloud "
                "http https www.  .com .org .edu .html "
                "read the article read the page open this"
            ),
            "habit_type": "action",
            "code_ref": "tools.ebook_reader:start_foreground_reading",
            "action": "tools.ebook_reader:start_foreground_reading",
            "why": "D107 foreground reading; URLs were falling through to background batch queue",
            "inertia": 0.30,
        },
    ),
    Memory(
        id="PROC_STOP_READING",
        narrative=(
            "When Akien says 'stop reading', 'stop background reading', or 'pause reading', "
            "I immediately set the stop flag and return 'One moment please…' — "
            "the reading loop finishes its current sentence then halts. "
            "This is the standard interrupt-acknowledgment pattern: "
            "acknowledge immediately, complete the atomic unit, then stop."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": (
                "stop reading stop background reading pause reading "
                "stop reading now pause the reading stop it"
            ),
            "habit_type": "action",
            "code_ref": "tools.ebook_reader:stop_foreground_reading",
            "action": "tools.ebook_reader:stop_foreground_reading",
            "why": "D107 one-moment-please interrupt pattern; general pattern to reuse",
            "inertia": 0.30,
        },
    ),
    Memory(
        id="PROC_QUEUE_FOR_INGEST",
        narrative=(
            "When Akien explicitly says 'queue this for ingestion', 'queue this for reading', "
            "'add to reading list', or 'add this to the queue', "
            "I add the URL or content to the background learn_queue for overnight batch processing. "
            "This is the batch path — NOT foreground reading. "
            "The distinction: 'read this' → foreground; 'queue this' → batch."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": (
                "queue this for ingestion queue this for reading add to reading list "
                "add this to the queue add to learn queue queue for later batch ingest"
            ),
            "habit_type": "response",
            "why": "D107 trigger disambiguation; prevents queue misfire when Akien wants foreground read",
            "inertia": 0.25,
        },
    ),
]

for mem in habits:
    existing = cortex.get(mem.id)
    if existing:
        cortex.store(mem)
        print(f"  updated  {mem.id}")
    else:
        cortex.store(mem)
        print(f"  seeded   {mem.id}")

print(f"\nDone. {len(habits)} foreground reading habit(s) seeded.")
