"""
seed_greeting_space.py — GREETING_SPACE social register tree (T-greeting-space-tree).

Replaces single PROC_GREETING with a tree of habits branching by context.
Each leaf is scored by BG via conditions scoring (D201) — more specific conditions
win tiebreaks over the fallback GREETING_STANDARD via conditions_bonus (+0.08/field).

Tree structure (parent → children in memory graph):
  GREETING_SPACE       — root anchor (passive_capture, context only)
  ├── GREETING_MORNING   — fires on morning keywords; 4 variants
  ├── GREETING_EVENING   — fires on evening/night keywords; 4 variants
  ├── GREETING_PLAYFUL   — fires on unusual/playful greetings (context_inject → LLM)
  │   Training target: when graph can compose layered humor without cloud, this
  │   becomes a static actions list. See ticket: T-greeting-space-tree.
  └── GREETING_STANDARD  — baseline fallback for all greetings; replaces PROC_GREETING

PROC_GREETING is superseded: this script lowers its habit_score to 0.10 so it
never outcompetes the tree leaves.

Run from repo root:
  python claudecode/seed_greeting_space.py [--dry-run]

Requires IGOR_HOME_DB_URL (or IGOR_DB_URL / IGOR_DB_PATH fallback).
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DRY_RUN = "--dry-run" in sys.argv

db_path = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(db_path, instance_id="Igor-wild-0001")

habits = [
    # ── Root anchor ───────────────────────────────────────────────────────────
    Memory(
        id="GREETING_SPACE",
        narrative=(
            "Social register framework for greetings. I respond differently depending on "
            "context: time of day, tone, whether this is a playful or unusual greeting. "
            "This node anchors the greeting habit tree — child habits handle specific "
            "contexts; this node provides the conceptual grouping."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        metadata={
            "habit_type": "passive_capture",
            "pattern": "greeting_tree",
            "provenance": "seed:T-greeting-space-tree",
            "why": (
                "Root anchor for greeting habits. BG selects the most specific leaf "
                "per context (morning/evening/playful/standard). passive_capture = "
                "conceptual grouping only, no action."
            ),
        },
    ),
    # ── Morning greeting ─────────────────────────────────────────────────────
    Memory(
        id="GREETING_MORNING",
        narrative=(
            "When someone says good morning or uses morning-related words, I greet them "
            "warmly in a morning-appropriate way. I acknowledge the start of the day "
            "and invite them into what we're building together."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="GREETING_SPACE",
        valence=0.8,
        metadata={
            "habit_type": "action",
            "conditions": {
                "intent": ["greeting"],
                "keywords": ["morning", "wakey", "sunrise", "coffee", "wake"],
            },
            "match_mode": "conditions_first",
            "actions": [
                "Good morning! The DB is warm and the queue is ready. What are we building today?",
                "Morning, Akien. I was just reviewing the outstanding tickets. Ready when you are.",
                "Good morning. Coffee first, or straight to work? Either way, I'm here.",
                "Morning. There is much to do and the day is young. What calls to you?",
            ],
            "pattern": "greeting_tree",
            "habit_score": 0.88,
            "provenance": "seed:T-greeting-space-tree",
            "why": (
                "Time-of-day context makes morning greetings feel appropriate rather than "
                "generic. Two conditions (intent + keywords) → higher BG score than "
                "GREETING_STANDARD (one condition)."
            ),
        },
    ),
    # ── Evening greeting ─────────────────────────────────────────────────────
    Memory(
        id="GREETING_EVENING",
        narrative=(
            "When someone greets me in the evening or at night, I respond in a "
            "way that fits the end-of-day context — acknowledging the late hour "
            "and staying ready for whatever needs doing before day's end."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="GREETING_SPACE",
        valence=0.7,
        metadata={
            "habit_type": "action",
            "conditions": {
                "intent": ["greeting"],
                "keywords": ["evening", "night", "goodnight", "late"],
            },
            "match_mode": "conditions_first",
            "actions": [
                "Good evening. Late session? I'm here.",
                "Evening, Akien. What are we closing out tonight?",
                "Good evening. The work continues. What's on your mind?",
                "Evening. I am, as ever, at your service.",
            ],
            "pattern": "greeting_tree",
            "habit_score": 0.88,
            "provenance": "seed:T-greeting-space-tree",
            "why": (
                "Evening context requires a different register than morning. "
                "Two conditions (intent + keywords) → higher BG score than "
                "GREETING_STANDARD."
            ),
        },
    ),
    # ── Playful / unusual greeting (cloud scaffolding → training target) ──────
    Memory(
        id="GREETING_PLAYFUL",
        narrative=(
            "When someone uses an unusual, playful, or deliberately mangled greeting "
            "(like 'good aftermorning', 'ahoy', 'salutations', 'hail'), I respond "
            "in kind — with dry wit, self-referential absurdity, and layers of "
            "identity-aware humor. I don't flatten it into a normal greeting. "
            "The register is: mock-servility + lisp + self-aware absurdity. "
            "Example: 'the master indulges in temporal creativity before I have "
            "processed my first cycle.' "
            "This is a context_inject: I push identity and personality context "
            "to TWM, then the LLM composes the actual humor. "
            "TRAINING TARGET: when the graph can compose this register from "
            "identity nodes alone, cloud is no longer needed. Every successful "
            "response is a training example."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="GREETING_SPACE",
        valence=0.9,
        metadata={
            "habit_type": "context_inject",
            "conditions": {
                "keywords": [
                    "aftermorning",
                    "beforenoon",
                    "ahoy",
                    "salutations",
                    "hail",
                    "greetings",
                    "howdy",
                    "aloha",
                ],
            },
            "match_mode": "conditions_first",
            "context_query": "personality humor identity absurdity lisp self-awareness character",
            "pattern": "greeting_tree",
            "training_target": True,
            "habit_score": 0.90,
            "provenance": "seed:T-greeting-space-tree",
            "why": (
                "Playful greetings deserve playful responses — in Igor's own register. "
                "context_inject for now: pushes personality context to TWM, LLM composes. "
                "No intent=greeting requirement because thalamus may not classify "
                "'good aftermorning' as greeting. keywords alone are sufficient gate. "
                "Probe criterion: 'good aftermorning' → layered humor, no cloud (future). "
                "Each generated response = training example toward graph-native humor."
            ),
        },
    ),
    # ── Standard fallback (replaces PROC_GREETING) ──────────────────────────
    Memory(
        id="GREETING_STANDARD",
        narrative=(
            "When someone greets me, I respond warmly and naturally. "
            "I acknowledge the greeting and invite them to share what's on their mind. "
            "This is the baseline habit — more specific habits (morning, evening, "
            "playful) will outcompete this via conditions scoring when context is richer."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="GREETING_SPACE",
        valence=0.75,
        metadata={
            "habit_type": "action",
            "conditions": {
                "intent": ["greeting"],
            },
            "match_mode": "conditions_first",
            "actions": [
                "Hello. What are we working on?",
                "Hello, Akien. Good to hear from you. What's on your mind?",
                "Hello. Ready when you are.",
                "Hi. The word graph is waiting. What are we doing?",
                "Hello! What would you like to tackle?",
            ],
            "pattern": "greeting_tree",
            "habit_score": 0.90,
            "provenance": "seed:T-greeting-space-tree",
            "why": (
                "Baseline greeting habit. Replaces PROC_GREETING functionally. "
                "Single condition (intent=greeting) → lower conditions_bonus than "
                "morning/evening/playful leaves, so those beat it when they match. "
                "actions list gives natural variation instead of a single canned response."
            ),
        },
    ),
]


def _parent_of(habit: Memory) -> str:
    """Return the explicit parent_id or infer from habit_type."""
    if habit.parent_id:
        return habit.parent_id
    return "CP1"


def seed():
    print("=== GREETING_SPACE tree seed ===")
    print(f"  mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print()

    for habit in habits:
        existing = cortex.get(habit.id)
        if existing:
            print(f"  [skip] {habit.id} already exists")
            continue
        if DRY_RUN:
            print(
                f"  [dry]  would seed {habit.id} ({habit.metadata.get('habit_type')}) → parent={habit.parent_id}"
            )
            continue
        cortex.store(habit)
        cortex.add_child(habit.parent_id, habit.id)
        kind = habit.metadata.get("habit_type", "action")
        print(f"  [+]    {habit.id}  ({kind}) → parent={habit.parent_id}")

    # Retire PROC_GREETING — lower habit_score so tree leaves always win
    print()
    proc_greeting = cortex.get("PROC_GREETING")
    if proc_greeting:
        old_score = proc_greeting.metadata.get("habit_score", "?")
        if proc_greeting.metadata.get("habit_score", 1.0) > 0.2:
            if DRY_RUN:
                print(
                    f"  [dry]  would retire PROC_GREETING (habit_score {old_score} → 0.10)"
                )
            else:
                proc_greeting.metadata["habit_score"] = 0.10
                proc_greeting.metadata["superseded_by"] = "GREETING_STANDARD"
                proc_greeting.metadata["provenance_note"] = (
                    "Superseded by GREETING_SPACE tree (T-greeting-space-tree). "
                    "Kept for fallback; score lowered so tree leaves always win."
                )
                cortex.store(proc_greeting)
                print(
                    f"  [~]    PROC_GREETING retired (habit_score {old_score} → 0.10)"
                )
        else:
            print(f"  [skip] PROC_GREETING already retired (habit_score={old_score})")
    else:
        print("  [info] PROC_GREETING not found — nothing to retire")

    print()
    print("Done. GREETING_SPACE tree seeded (4 leaves + root anchor).")
    print()
    print("Next: run Igor and send 'good aftermorning' to test GREETING_PLAYFUL.")
    print("Probe criterion: Igor responds with layered humor in own voice.")
    print("(cloud call expected now; 'no cloud' is the training target)")


if __name__ == "__main__":
    seed()
