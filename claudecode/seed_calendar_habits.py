#!/usr/bin/env python3
"""
seed_calendar_habits.py — Seed calendar usage habits (#166).

Run once. Safe to re-run (upsert).
Usage: python claudecode/seed_calendar_habits.py
"""
import sys, os
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

env_path = Path.home() / ".TheIgors" / "igor_wild_0001" / ".env"
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
    Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"
))
cortex = Cortex(DB_PATH)

MEMORIES = [
    Memory(
        id="PROC_CALENDAR_CREATE",
        narrative=(
            "When I need to remember to do something at a specific time, create a calendar event "
            "via create_calendar_event(). When it's a task without a fixed time, use create_task(). "
            "Use the description field to record why I set the reminder — context I'll need when it fires. "
            "Events for meetings/commitments; tasks for actionable to-dos with a due date."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.7,
        metadata={
            "trigger": "remind me schedule remember set reminder task",
            "habit_type": "workflow",
            "action": "create_calendar_event|create_task",
            "parent_cp": "CP4",
            "github_issue": "166",
            "inertia": "0.45",
        },
    ),
    Memory(
        id="PROC_CALENDAR_ALERT_RESPOND",
        narrative=(
            "When a CALENDAR_ALERT appears in my TWM (thread_id starts with 'calendar:'), "
            "it is a self-contained episodic unit — the complete context for that commitment. "
            "Read the event title and description, do what I committed to do, then "
            "mark the task complete via complete_task() or acknowledge the event. "
            "Calendar alerts are not ambient background — they are explicit attention claims."
        ),
        memory_type=MemoryType.PROCEDURAL,
        activation_count=0,
        valence=0.75,
        metadata={
            "trigger": "CALENDAR_ALERT reminder event due task alert",
            "habit_type": "response",
            "action": "complete_task|list_calendar_events",
            "parent_cp": "CP1",
            "github_issue": "166",
            "inertia": "0.5",
        },
    ),
    Memory(
        id="FACTUAL_CALENDAR_ARCHITECTURE",
        narrative=(
            "Igor's calendar is tied to theigorsigor@gmail.com (Google Calendar + Tasks). "
            "Notifications arrive as email — Igor reads them via IMAP like any other email, "
            "no polling needed. The Calendar API is only used for creating/managing events (write side). "
            "OAuth2 credentials at ~/.TheIgors/igor_wild_0001/google_credentials.json. "
            "Employer calendars use separate credentials — providing them constitutes consent. "
            "Calendar reminder emails are episodic attention units: bounded, self-contained, "
            "handled and closed like any actionable email."
        ),
        memory_type=MemoryType.FACTUAL,
        activation_count=0,
        valence=0.6,
        metadata={
            "tags": ["calendar", "google", "setup", "architecture"],
            "github_issue": "166",
            "inertia": "0.4",
        },
    ),
    Memory(
        id="INTERPRETIVE_CALENDAR_VS_CHANNEL",
        narrative=(
            "Calendar alerts and open channels (web UI, Discord) are architecturally distinct: "
            "a calendar alert is an episodic attention nexus — bounded, self-contained, "
            "closes when acted on. An open channel is a continuous nexus — unbounded traffic, "
            "persistent context. This distinction matters for TWM scope and attention routing: "
            "calendar thread_ids are ephemeral, channel thread_ids are persistent."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        activation_count=0,
        valence=0.7,
        metadata={
            "direction": "upward",
            "condition": "routing attention between calendar and channel inputs",
            "meaning_payload": "episodic vs continuous nexus have different TTL and cleanup semantics",
            "action_pointer": "PROC_CALENDAR_ALERT_RESPOND",
            "parent_cp": "CP3",
            "github_issue": "166",
            "inertia": "0.5",
        },
    ),
]

for m in MEMORIES:
    cortex.store(m)
    print(f"  seeded {m.id}")

print(f"Done. {len(MEMORIES)} memories seeded.")
