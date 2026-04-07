"""
seed_cluster_ssh_habit.py — G49: SSH cluster health reactive habit.

Closes the gap where Igor escalates to LLM when asked "are the boxes up?"
cluster_status() in tools/cluster_ssh.py already does the work:
  - SSH echo check per machine (ssh -i igor_id_rsa ... echo ssh_ok)
  - Ollama HTTP health check per machine
  - Returns a one-line summary table

This habit wires trigger phrases to that tool, with a 5-min TWM TTL
(cluster state is slow-changing; no need to re-check every 30s).

Run from repo root:
  python claudecode/seed_cluster_ssh_habit.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"))

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

habits = [
    Memory(
        id="PROC_CLUSTER_SSH_CHECK",
        narrative=(
            "When Akien asks whether the cluster machines are up — 'are the boxes up', "
            "'cluster status', 'check ssh', 'which machines are online' — I do not guess. "
            "I have a tool that SSHes to each box and echoes back, then checks Ollama health. "
            "I run it and report the result directly. "
            "The answer is good for a few minutes; no need to re-run until something changes. "
            "If a box is down, I say which one. If they're all up, I say that clearly too."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "trigger": (
                "boxes up ssh cluster status online machines check ssh "
                "are boxes up which machines reachable cluster health"
            ),
            "habit_type": "action",
            "code_ref": "tools.cluster_ssh:_cluster_status",
            "twm_ttl_seconds": 300,
            "why": (
                "G49: Igor was escalating to LLM and hallucinating cluster state. "
                "cluster_status() does real SSH echo checks. "
                "Reactive habit = no LLM needed, fast, accurate."
            ),
            "inertia": 0.25,
        },
    ),
]

for h in habits:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP1", h.id)
    print(f"  [seeded] {h.id}  (action) → parent=CP1")

print("Done.")
