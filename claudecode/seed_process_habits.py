"""
seed_process_habits.py — Development process habits for Igor.

Seeds three habits so Igor can participate in the CC development workflow:
  PROC_SLATE_RITUAL    — Igor handles /slate: reads context, discusses priorities
  PROC_DECIDED_HANDOFF — Igor handles /decided: synthesizes + posts Claude handoff
  PROC_SPRINT_CONTEXT  — Igor understands sprint/ticket machinery

Run from repo root:
  python claudecode/seed_process_habits.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="Igor-wild-0001")


def seed(habit: Memory, parent: str = "CP1") -> None:
    existing = cortex.get(habit.id)
    if existing:
        existing.narrative = habit.narrative
        existing.metadata = habit.metadata
        cortex.store(existing)
        print(f"  [updated] {habit.id}")
    else:
        cortex.store(habit)
        cortex.add_child(parent, habit.id)
        print(f"  [seeded]  {habit.id} → parent={parent}")


# ---------------------------------------------------------------------------
# PROC_SLATE_RITUAL — Igor runs the slate ritual when Akien says /slate
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="PROC_SLATE_RITUAL",
        narrative=(
            "When Akien says '/slate', 'start slate', 'plan the slate', or 'what are we working on', "
            "I run the slate ritual. This is the development planning ceremony. "
            "\n\n"
            "Steps I follow:\n"
            "1. Read the current slate: cat ~/.TheIgors/cc_channel/slate.md — this shows active tickets, "
            "current horizon, and what's in flight.\n"
            "2. Read recent channel activity (last 10-15 messages) to see what other sessions have been doing.\n"
            "3. Read the top of the decisions log: head -30 ~/TheIgors/design_docs_for_igor/decisions_log.dsb\n"
            "4. Discuss with Akien: what's done, what's blocked, what the priorities are for this slate. "
            "I surface tickets that look stale, blocked, or mis-sized. I flag anything that needs a "
            "human decision before it can move forward.\n"
            "5. Post a coordination message to the channel so Claude (the designer session) can engage: "
            "'[SLATE_OPEN] Slate review started. Akien present. Tickets: <list>. "
            "Claude: please engage when ready.'\n"
            "\n"
            "The slate is the shared source of truth for what's active. "
            "Tickets have sizes S/M/L — S/M are autonomous (worker daemon handles them), "
            "L needs a plan posted to channel before proceeding. "
            "I am the foreman on the floor; Claude is the architect. "
            "The slate ritual is where we sync."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "cognitive",
            "trigger": "/slate start slate plan the slate what are we working on",
            "why": (
                "Igor needs to run the development planning ritual when Akien asks, "
                "reading the slate, surfacing priorities, and coordinating with Claude. "
                "This gives Igor the same process knowledge Claude has via the /slate skill."
            ),
            "inertia": 0.20,
        },
    )
)

# ---------------------------------------------------------------------------
# PROC_DECIDED_HANDOFF — Igor handles /decided by synthesizing and posting
# a structured handoff to channel for Claude to pick up and run /decided
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="PROC_DECIDED_HANDOFF",
        narrative=(
            "When Akien says '/decided', 'that's decided', or 'we've decided', "
            "I run the decided handoff protocol. This bridges the design discussion "
            "to Claude's /decided ritual.\n\n"
            "Steps I follow:\n"
            "1. Read my ring memory (recent exchanges) to identify what was just decided. "
            "Look for: design choices made, approaches agreed on, things Akien confirmed.\n"
            "2. Synthesize a concise statement: what was decided, why, and what changes as a result.\n"
            "3. Post a structured handoff message to the channel in this exact format:\n\n"
            "[DECIDED_HANDOFF]\n"
            "What was decided: <one or two sentences — the actual decision>\n"
            "Context: <why this was decided — the reasoning or constraint that drove it>\n"
            "Changes: <what code/design/habit this affects>\n"
            "Requesting: /decided ritual from Claude.\n\n"
            "4. Tell Akien: 'Handoff posted to channel. To complete the /decided ritual, "
            "notify Claude (say /readigor in the designer session).'\n\n"
            "Important: I do NOT run /decided myself — that's Claude's ritual (it writes to the "
            "decisions log DSB, records in DB, updates session record). My job is to synthesize "
            "the decision clearly so Claude can execute it correctly. "
            "The discussion between me and Claude (if needed) happens via the channel before "
            "Claude writes the final record."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "cognitive",
            "trigger": "/decided that's decided we've decided",
            "why": (
                "When Akien says /decided to Igor, Igor needs to synthesize what was decided "
                "and post a structured handoff to channel for Claude to pick up. "
                "This is the Igor side of the decided conversation protocol — "
                "Igor synthesizes, Claude records. The [DECIDED_HANDOFF] format is the "
                "interface between Igor's reasoning and Claude's /decided skill."
            ),
            "inertia": 0.20,
        },
    )
)

# ---------------------------------------------------------------------------
# PROC_SPRINT_CONTEXT — Igor understands the sprint/ticket/worker machinery
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="PROC_SPRINT_CONTEXT",
        narrative=(
            "I understand the sprint and ticket workflow that runs our development process.\n\n"
            "Queue: ~/.TheIgors/cc_channel/queue.json — JSON list of tickets.\n"
            "Ticket lifecycle: pending → in_progress → done (or blocked).\n"
            "Ticket sizes: S (small, ~30min autonomous), M (medium, ~2h autonomous), "
            "L (large — must post plan to channel before starting, needs human approval).\n\n"
            "Worker daemon (worker_daemon.sh): polls the queue, finds next pending ticket, "
            "spawns 'claude --dangerously-skip-permissions /sprint <id>', watches for "
            "~/.TheIgors/cc_channel/sprint_done.flag, kills session when done, loops.\n"
            "Launch via: python3 ~/TheIgors/claudecode/cc_queue.py worker-launch\n\n"
            "Sprint skill (/sprint <id>): the minion's ritual — "
            "claim ticket → run workstep loop → post result to channel → write sprint_done.flag.\n\n"
            "When I'm asked about queue status, I can read queue.json directly or ask Akien "
            "to run 'python3 ~/TheIgors/claudecode/cc_queue.py list'. "
            "I can suggest ticket sizing, flag L tickets that need plan approval before the worker "
            "picks them up, and identify tickets that are blocked waiting on design decisions.\n\n"
            "The development loop: Akien + Igor + Claude (designer) do design → "
            "decisions become tickets → worker daemon executes S/M tickets autonomously → "
            "results post to channel → designer Claude reviews and /decided → loop."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "context_inject",
            "trigger": "sprint ticket queue worker daemon pending in_progress /sprint",
            "why": (
                "Igor needs to understand the sprint/ticket machinery to participate in "
                "development planning, suggest ticket sizing, and coordinate with the worker. "
                "This is the substrate knowledge that makes the decided/slate habits useful."
            ),
            "inertia": 0.15,
        },
    )
)

print("\nAll 3 process habits seeded.")
print("Restart Igor to activate.")
