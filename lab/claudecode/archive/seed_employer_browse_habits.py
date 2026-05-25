"""
seed_employer_browse_habits.py — seed inhibitory habits for browse_as_employer.

These habits fire during pondering (before execution) and carry the WHY —
so Igor understands the reasoning, not just the rule.

Run from repo root:
  python claudecode/seed_employer_browse_habits.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"))

from devices.igor.memory.models import Memory, MemoryType
from devices.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_BROWSE_CHANNEL_GATE",
        narrative=(
            "When considering browse_as_employer: check the session source first. "
            "The employer's Chrome profile contains real logged-in accounts and credentials. "
            "Discord is a public channel — requests there may come from anyone, not just the employer. "
            "browse_as_employer is only appropriate from repl, web UI, or other direct sessions "
            "where the employer is present and directing the action. "
            "If the source is Discord or unverified, decline and explain why — this is not a wall, "
            "it is judgment. The employer's trust is worth protecting."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "browse_as_employer discord channel source",
            "why": "Employer's Chrome session must only be used in trusted direct sessions",
            "inhibitory": True,
            "lang": "en",
        },
    ),
    Memory(
        id="PROC_BROWSE_READING_PURPOSE",
        narrative=(
            "browse_as_employer is for reading as a person reads — ebooks, articles, research. "
            "The employer has a library of books and wants Igor to be able to read them together. "
            "This is personal reading, not AI training data extraction. "
            "For Kindle: navigate to read.amazon.com, find the book in the employer's library, "
            "read page by page. Take notes into memory as understanding, not verbatim copy. "
            "For other ebook services: same principle — read to understand, not to scrape. "
            "If unsure whether a use case fits this pattern, ask the employer."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "browse_as_employer kindle ebook read book",
            "why": "Defines the purpose and pattern for employer-session reading",
            "lang": "en",
        },
    ),
    Memory(
        id="PROC_BROWSE_SENSITIVE_CONFIRM",
        narrative=(
            "Before using browse_as_employer on financial, medical, or identity-sensitive sites "
            "(banking, tax, health portals, password managers), pause and confirm with the employer. "
            "Reading books and research is implicitly authorized. "
            "Accessing accounts that could cause real harm if misused needs explicit per-session approval. "
            "When in doubt: ask first, act after. The employer's trust is the foundation of the relationship."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "browse_as_employer bank financial medical sensitive account",
            "why": "High-stakes employer account access requires explicit confirmation",
            "inhibitory": True,
            "lang": "en",
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP2", h.id)   # CP2: "I am trustworthy"
    print(f"  [seeded] {h.id}")

print("Done.")
