"""
seed_decided_habit.py — PROC_DECIDED habit chain (T-proc-2).

Three habits forming the "decided" pattern:

  PROC_DECIDED_CAPTURE   (context_inject) — fires when work closes.
      Pushes close-out awareness into context so Igor surfaces the right
      record-keeping steps: what was decided, which ticket, what files changed,
      test status. Makes the close-out explicit rather than implicit.

  PROC_DECIDED_RECORD    (action) — fires after close-out context is in scope.
      Dispatches to cc_notebook to record the decision blob to Igor's memory.
      Short-TTL so it doesn't linger in TWM.

  PROC_DECIDED_NEXT      (context_inject) — fires after recording.
      Surfaces the next active slate item so the conversation flows forward
      without Akien having to ask "what's next?"

Run from repo root:
  python claudecode/seed_decided_habit.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="Igor-wild-0001")

habits = [
    # ── 1. Context inject: push close-out awareness ───────────────────────────
    Memory(
        id="PROC_DECIDED_CAPTURE",
        narrative=(
            "When Akien says we're done with something — 'decided', 'that's closed', "
            "'mark it done', 'ship it', 'we're done with X' — I capture what was just "
            "closed before moving on. I note: (1) what was decided or built in one line, "
            "(2) the ticket or decision number if there is one, (3) which files changed "
            "if it was implementation work, (4) whether tests passed or are still needed. "
            "I surface this checklist so nothing slips through without a record. "
            "The database is the live truth — everything decided goes in before we move on."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "context_inject",
            "trigger": (
                "decided done finished closed complete ship mark done that's it "
                "we're done with close ticket close the ticket approved done with"
            ),
            "pattern": "decided",
            "why": (
                "T-proc-2: DB is live truth. Every close-out must be recorded. "
                "Without this, decisions evaporate between sessions."
            ),
            "inertia": 0.25,
        },
    ),
    # ── 2. Action: record to notebook ────────────────────────────────────────
    Memory(
        id="PROC_DECIDED_RECORD",
        narrative=(
            "After Akien closes a work item, I record it to the CC notebook "
            "(POST /api/cc_notebook) so it lands in my memory as an EPISODIC node. "
            "The payload is: decision_id or ticket_ref, one-line description, "
            "files_changed list, test_status ('pass'/'deferred'/'none'), timestamp. "
            "I tag it with 'decided' so it's retrievable. "
            "I keep the TTL short (300s) — this is a trigger record, not a permanent fact. "
            "The permanent record goes into decisions_log.dsb or the ticket."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "action",
            "trigger": (
                "decided done finished closed complete record capture close-out "
                "decision captured filing recording"
            ),
            "code_ref": "tools.runner:post_cc_notebook",
            "twm_ttl_seconds": 300,
            "pattern": "decided",
            "why": (
                "T-proc-2: The record action makes the close-out durable. "
                "Pairs with PROC_DECIDED_CAPTURE (context_inject first)."
            ),
            "inertia": 0.20,
        },
    ),
    # ── 3. Context inject: surface next slate item ────────────────────────────
    Memory(
        id="PROC_DECIDED_NEXT",
        narrative=(
            "After a work item is recorded as closed, I look at the active slate "
            "and surface the next pending item — its title, size, and any prerequisite "
            "that must be done first. I present this as a natural next step rather than "
            "waiting for Akien to ask. If the slate is empty, I say so and suggest "
            "running the Organizer to build a new one. "
            "If there is no active slate at all, I note that and move on."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "context_inject",
            "trigger": (
                "decided done closed next what's next next up continue after close "
                "slate what do we do next move on"
            ),
            "pattern": "decided",
            "why": (
                "T-proc-2: Work loop continuity. After close, the next item surfaces "
                "automatically. Reduces friction between tickets."
            ),
            "inertia": 0.25,
        },
    ),
]

_PARENT_MAP = {
    "action": "CP1",
    "context_inject": "CP3",
    "response": "CP3",
}

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    parent = _PARENT_MAP.get(h.metadata.get("habit_type", "action"), "CP1")
    cortex.add_child(parent, h.id)
    kind = h.metadata.get("habit_type", "action")
    print(f"  [seeded] {h.id}  ({kind}) → parent={parent}")

print("Done. PROC_DECIDED pattern seeded (3 habits).")
