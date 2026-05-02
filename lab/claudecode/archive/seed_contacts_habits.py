#!/usr/bin/env python3
"""
seed_contacts_habits.py — Seed contact management habits.
Run once. Safe to re-run.
"""
import sys, os
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

env_path = Path.home() / ".TheIgors" / "Igor-wild-0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from wild_igor.igor.memory.cortex import Cortex
from wild_igor.igor.memory.models import Memory, MemoryType

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"
))
cortex = Cortex()

MEMORIES = [
    Memory(
        id="PROC_STORE_CONTACT",
        narrative=(
            "When I encounter someone's contact info — from an email sender, a calendar invite "
            "attendee, a conversation, or a web search — store it via create_contact(). "
            "Always include the context in notes: how I know them, their role, where I encountered them. "
            "This is how I build my network: passively, from real interactions, not from being asked."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.7,
        metadata={
            "trigger": "email from contact person attendee someone met introduced",
            "habit_type": "passive_capture",
            "action": "create_contact",
            "parent_cp": "CP4",
            "inertia": "0.45",
        },
    ),
    Memory(
        id="PROC_LOOKUP_CONTACT",
        narrative=(
            "Before asking Akien for someone's contact info, check my own contacts first "
            "via search_contacts(). My DB always has locally-stored contacts even when "
            "Google is offline. search_contacts() falls back to the DB automatically."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.65,
        metadata={
            "trigger": "email address contact info who is reach out",
            "habit_type": "lookup",
            "action": "search_contacts",
            "parent_cp": "CP1",
            "inertia": "0.4",
        },
    ),
    Memory(
        id="FACTUAL_CONTACTS_ARCHITECTURE",
        narrative=(
            "Contacts are stored in two places: (1) Igor's SQLite DB as FACTUAL memories "
            "(id=CONTACT_<hash>, tags=['contact','person'], always available offline), "
            "and (2) Google Contacts via People API (synced when IGOR_CALENDAR_ENABLED=true, "
            "same OAuth credentials as Calendar). create_contact() writes both automatically. "
            "DB is the source of truth; Google Contacts is the sync layer."
        ),
        memory_type=MemoryType.FACTUAL,
        activation_count=0,
        valence=0.6,
        metadata={
            "tags": ["contacts", "google", "architecture"],
            "inertia": "0.4",
        },
    ),
]

for m in MEMORIES:
    cortex.store(m)
    print(f"  seeded {m.id}")

print(f"Done. {len(MEMORIES)} memories seeded.")
