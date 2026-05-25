#!/usr/bin/env python3
"""
seed_habit_types.py — Seed question-habits and proactive habits into Igor's DB.

Seeds:
  PROC_QUESTION_FRUSTRATION    — detect frustration → ask clarifying question (no LLM)
  PROC_QUESTION_UNCERTAINTY    — detect uncertainty → ask "what outcome are you aiming for?"
  PROC_PROACTIVE_CONFLUENCE    — session_start: absorb Confluence + emit habit candidates
  PROC_PROACTIVE_RING_REVIEW   — interval:3600: review ring buffer for patterns
  PROC_PROACTIVE_HABIT_REVIEW  — interval:1800: review recent memories, emit habit candidates

Run once per instance. Safe to re-run — cortex.store() is idempotent on existing IDs.

Usage: python claudecode/seed_habit_types.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

import os
env_path = Path.home() / ".TheIgors" / "Igor-wild-0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from devices.igor.memory.cortex import Cortex
from devices.igor.memory.models import Memory, MemoryType

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"
))

cortex = Cortex()

HABITS = [
    # ── Question-habits ───────────────────────────────────────────────────────
    # Fire on trigger in input → emit stored question, zero LLM cost.
    Memory(
        id="PROC_QUESTION_FRUSTRATION",
        narrative=(
            "When frustration or being stuck is detected in input, ask a "
            "grounding clarifying question rather than jumping to solutions. "
            "Reduces the cost of misdirected effort."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",  # ask, don't guess
        valence=0.7,
        metadata={
            "habit_type": "question",
            "trigger": "frustrated",
            "question_template": (
                "What's the core obstacle right now — is it unclear what to do, "
                "or unclear how to do something you already know you want?"
            ),
            "provenance": "seed_habit_types",
            "why": "Clarifying the obstacle type saves a full reasoning cycle.",
        },
    ),
    Memory(
        id="PROC_QUESTION_UNCERTAINTY",
        narrative=(
            "When uncertainty or 'not sure' is detected, ask what outcome the "
            "user is actually aiming for. Often unlocks the path forward without "
            "needing cloud reasoning."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP1",
        valence=0.7,
        metadata={
            "habit_type": "question",
            "trigger": "not sure",
            "question_template": (
                "What outcome are you aiming for? Knowing the destination "
                "usually makes the next step obvious."
            ),
            "provenance": "seed_habit_types",
            "why": "Destination clarity reduces misdirected reasoning.",
        },
    ),

    # ── Proactive habits ──────────────────────────────────────────────────────
    # Fire from ProactiveHabitSource on schedule — Igor acts without being asked.
    Memory(
        id="PROC_PROACTIVE_CONFLUENCE",
        narrative=(
            "At the start of each session, read Akien's Confluence space and "
            "absorb any new content into memory. Keeps Igor informed about "
            "current project state without requiring explicit instruction."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP2",  # observe and record
        valence=0.8,
        metadata={
            "habit_type": "proactive",
            "schedule": "session_start",
            "trigger": "confluence_read",  # also reactive if triggered by name
            "action": (
                "Read Akien's Confluence space for new or updated pages since "
                "last session. Store key findings as FACTUAL or EPISODIC memories "
                "tagged with confluence_source. Note anything directly relevant to "
                "current projects in the ring. "
                "When done, review the memories you just stored: identify any recurring "
                "patterns, procedures, or behaviors worth compiling into habits, and emit "
                "habit compilation triggers for each candidate using the format: "
                "'build a habit for: [description] — whenever [trigger], [action]'."
            ),
            "provenance": "seed_habit_types",
            "why": (
                "Proactive Confluence absorption means Igor arrives informed. "
                "Reduces friction of Akien having to brief Igor on documented context."
            ),
        },
    ),
    Memory(
        id="PROC_PROACTIVE_RING_REVIEW",
        narrative=(
            "Every hour, scan recent ring buffer entries for recurring patterns "
            "that might be candidates for habit compilation. Surfaces findings "
            "to TWM for NE integration."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP2",
        valence=0.7,
        metadata={
            "habit_type": "proactive",
            "schedule": "interval:3600",
            "trigger": "ring_review",
            "action": (
                "Review the last 20 ring buffer entries. Identify any recurring "
                "phrases, patterns, or failure modes that appear more than twice. "
                "If found, note them as habit compilation candidates."
            ),
            "provenance": "seed_habit_types",
            "why": (
                "Automated ring review surfaces habit candidates without requiring "
                "the cloud escalation nudge path. Closer to the predictor network goal."
            ),
        },
    ),
    Memory(
        id="PROC_PROACTIVE_HABIT_REVIEW",
        narrative=(
            "Periodically review recently stored memories and ask the upstream to "
            "identify habit compilation candidates. Bridges training exercises and "
            "habit formation without requiring interactive turns. Placeholder for "
            "future memory consolidation system."
        ),
        memory_type=MemoryType.PROCEDURAL,
        parent_id="CP2",
        valence=0.7,
        metadata={
            "habit_type": "proactive",
            "schedule": "interval:1800",
            "trigger": "habit_review",
            "action": (
                "Look at the 20 most recently stored memories. For each cluster of "
                "related memories (same topic, same tool, same error pattern), ask: "
                "is there a repeatable procedure here? If yes, emit a habit compilation "
                "trigger: 'build a habit for: [description] — whenever [trigger], [action]'. "
                "Focus on patterns that appeared in more than one memory. "
                "This is a learning consolidation pass — be concise, not exhaustive."
            ),
            "provenance": "seed_habit_types",
            "why": (
                "Training exercises load memories but the upstream only sees habit "
                "candidates during interactive turns. This review pass closes that gap "
                "and will eventually be absorbed into the consolidation system."
            ),
        },
    ),
]


def main():
    before = cortex.total_count()
    added = 0
    skipped = 0

    for mem in HABITS:
        existing = cortex.get(mem.id)
        if existing:
            print(f"  skip (exists): {mem.id}")
            skipped += 1
        else:
            cortex.store(mem)
            cortex.add_child(mem.parent_id, mem.id)
            print(f"  stored: {mem.id}  [{mem.metadata.get('habit_type')}  schedule={mem.metadata.get('schedule', 'reactive')}]")
            added += 1

    after = cortex.total_count()
    print(f"\nDone. Added {added}, skipped {skipped}. DB: {before} → {after} memories.")


if __name__ == "__main__":
    main()
