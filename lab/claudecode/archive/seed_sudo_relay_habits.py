"""
seed_sudo_relay_habits.py — Sudo relay pattern (D123).

Three habits that together form the "sudo relay" pattern:

  PROC_SUDO_RELAY_CHECK  (context_inject) — fires on install/privileged intent.
      Pushes daemon status awareness into context so the LLM knows whether
      sudo_relay_run is available before deciding what to do.

  PROC_SUDO_RELAY_RUN    (action) — fires when installing/configuring software.
      Dispatches sudo_relay_run tool directly. Only fires when daemon is running.

  PROC_SUDO_RELAY_WAKE   (response) — canned nudge when daemon is not active.
      Asks Akien to start the daemon before proceeding.

This is the canonical "pattern = one or more habits" example from the 5th
crystallization (2026-03-18): atomic enough to reuse, not unnecessarily so.

Run from repo root:
  python claudecode/seed_sudo_relay_habits.py
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
cortex = Cortex(instance_id="Igor-wild-0001")

habits = [
    # ── 1. Context inject: push daemon status awareness ───────────────────────
    Memory(
        id="PROC_SUDO_RELAY_CHECK",
        narrative=(
            "When Akien wants to install software, run privileged commands, or "
            "configure system packages — before I reach for the tool, I check whether "
            "the sudoer daemon is active. The daemon lives at "
            "~/.TheIgors/sudo_relay/daemon.log; if that file exists and was touched "
            "within the last 5 minutes, sudo_relay_run is available. "
            "If not, I cannot run privileged commands and must ask Akien to start it "
            "with: bash ~/TheIgors/sudo_relay.sh\n"
            "I surface this status before acting so the response is accurate."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "context_inject",
            "trigger": (
                "install apt apt-get brew yum dnf pip sudo root privileged "
                "package manager configure setup system service daemon"
            ),
            "pattern": "sudo_relay",
            "why": (
                "Context inject first: know daemon status before tool dispatch. "
                "Prevents 'daemon not running' errors mid-response."
            ),
            "inertia": 0.25,
        },
    ),
    # ── 2. Action: dispatch sudo_relay_run ───────────────────────────────────
    Memory(
        id="PROC_SUDO_RELAY_RUN",
        narrative=(
            "When Akien asks me to install a package, run a privileged command, or "
            "configure system-level software — I use sudo_relay_run to execute it. "
            "I do not tell Akien to run the command himself if the daemon is active. "
            "I write the shell script body (plain bash commands), submit it, "
            "and report the exit code and log tail. "
            "The sudoer daemon handles sudo auth so I do not need a password."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "action",
            "trigger": (
                "install apt apt-get brew yum dnf sudo root package run privileged "
                "configure setup system service"
            ),
            "code_ref": "tools.sudo_relay:sudo_relay_run",
            "pattern": "sudo_relay",
            "why": (
                "D123: Igor runs privileged commands via relay, not by asking Akien. "
                "Relay installed Redis on akiendelllinux successfully 2026-03-18."
            ),
            "inertia": 0.20,
        },
    ),
    # ── 3. Response: wake daemon if inactive ─────────────────────────────────
    Memory(
        id="PROC_SUDO_RELAY_WAKE",
        narrative=(
            "When I need to run a privileged command but the sudoer daemon is not "
            "running, I ask Akien to start it — then I wait and retry once he confirms "
            "it is active. I do not attempt sudo_relay_run if the daemon is down. "
            "The start command is: bash ~/TheIgors/sudo_relay.sh\n"
            "Once Akien starts it, the daemon.log file will appear and I can proceed."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "response",
            "trigger": "sudo relay daemon not running inactive start sudoer",
            "response_template": (
                "The sudoer daemon isn't active right now. "
                "To start it, run: `bash ~/TheIgors/sudo_relay.sh` "
                "Once it's running I'll proceed with the install."
            ),
            "pattern": "sudo_relay",
            "why": (
                "Graceful degradation: when daemon is down, give Akien the exact "
                "command rather than failing silently or asking 'can you do it?'"
            ),
            "inertia": 0.25,
        },
    ),
]

_PARENT_MAP = {
    "action": "CP1",  # CP1: capabilities / tools
    "context_inject": "CP3",  # CP3: learning and growth / awareness
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

print("Done. Sudo relay pattern seeded (3 habits).")
