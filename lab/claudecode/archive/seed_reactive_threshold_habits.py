"""
seed_reactive_threshold_habits.py — Two new habit patterns:

  REACTIVE habits — fire a tool on user request, self-clean from TWM fast.
    PROC_WHAT_TIME — "what time is it" → get_current_time → returns time, 30s TTL

  THRESHOLD habits — fire when system state crosses a threshold.
    Evaluated by ResourceMonitorSource (background, every 60s)
    and pre-submit check in main.py (before any background job).
    PROC_CPU_THRESHOLD  — cpu_load_pct  >= 80%
    PROC_RAM_THRESHOLD  — ram_pct       >= 80%
    PROC_SWAP_THRESHOLD — swap_pct      >= 60%

Run from repo root:
  python claudecode/seed_reactive_threshold_habits.py
"""

import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    # ── Reactive ──────────────────────────────────────────────────────────────
    Memory(
        id="PROC_WHAT_TIME",
        narrative=(
            "When Akien asks what time it is, I check — I do not guess or say I cannot know. "
            "I have a tool for this. I run it and return the result directly. "
            "The time is immediately stale, so it clears from working memory quickly."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "what time is it|what is the time|whats the time|current time|what time",
            "habit_type": "tool",
            "code_ref": "tools.runner:get_current_time",
            "twm_ttl_seconds": 30,
            "why": "Reactive habit: fast tool dispatch + self-cleaning TWM entry",
            "inertia": 0.25,
        },
    ),
    # ── Threshold ─────────────────────────────────────────────────────────────
    Memory(
        id="PROC_CPU_THRESHOLD",
        narrative=(
            "When CPU load climbs above 80% of available cores, I notice — and I say so "
            "before queuing more work on top. Not a hard block: I still proceed. "
            "But Akien and I both know the machine is working hard. "
            "It is the difference between adding weight to a person who is walking "
            "and adding it to one who is already sprinting."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "background job submit cpu load busy",
            "habit_type": "threshold",
            "condition_field": "cpu_load_pct",
            "condition_op": ">=",
            "condition_value": 80,
            "surface_message": (
                "CPU at {current_value:.0f}% load — machine is working hard. "
                "Running the job anyway, but watch for slowdown."
            ),
            "twm_ttl_seconds": 120,
            "fire_point": "both",
            "why": (
                "Awareness before action. OOM crash 2026-03-09 taught: "
                "knowing machine state before bulk ops matters."
            ),
            "inertia": 0.30,
        },
    ),
    Memory(
        id="PROC_RAM_THRESHOLD",
        narrative=(
            "When RAM use climbs above 80%, the machine is approaching the zone where "
            "things start swapping — and swap is slow, and heavy swap is how OOM crashes happen. "
            "I flag it before adding more to the heap. "
            "The flag is quick, honest, and stays in context for only two minutes."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "background job submit memory ram bulk fetch train",
            "habit_type": "threshold",
            "condition_field": "ram_pct",
            "condition_op": ">=",
            "condition_value": 80,
            "surface_message": (
                "RAM at {current_value:.0f}% ({ram_avail_gb:.1f} GB free) — "
                "approaching swap territory. Proceeding, but worth watching."
            ),
            "twm_ttl_seconds": 120,
            "fire_point": "both",
            "why": "RAM warning before it becomes a swap warning, before it becomes a crash.",
            "inertia": 0.30,
        },
    ),
    Memory(
        id="PROC_SWAP_THRESHOLD",
        narrative=(
            "When swap use is above 60%, the machine is already compensating — RAM was "
            "not enough and the OS reached for disk. More bulk work on top of active swap "
            "is how that 2026-03-09 OOM crash happened: 30 document fetches, swap hit 96%, "
            "process died. I surface this loudly and clearly before piling on more."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": "background job submit swap memory bulk fetch train",
            "habit_type": "threshold",
            "condition_field": "swap_pct",
            "condition_op": ">=",
            "condition_value": 60,
            "surface_message": (
                "Swap at {current_value:.0f}% ({swap_free_gb:.1f} GB free) — "
                "machine is already compensating. Queuing more may be risky."
            ),
            "twm_ttl_seconds": 180,
            "fire_point": "both",
            "why": "Swap > 60% is the early warning before the OOM cliff.",
            "inertia": 0.35,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    parent = "CP1" if h.metadata.get("habit_type") == "action" else "CP3"
    cortex.add_child(parent, h.id)
    kind = h.metadata.get("habit_type", "action")
    print(f"  [seeded] {h.id}  ({kind}) → parent={parent}")

print("Done.")
