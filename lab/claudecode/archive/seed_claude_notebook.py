"""
seed_claude_notebook.py — #239: seed Claude's employer notebook in Igor's DB.

These are Claude's persistent cross-session working notes — the things Claude
needs to remember about the project that shouldn't live only in a context window.

Run from repo root:
  python claudecode/seed_claude_notebook.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)

from devices.igor.memory.models import Memory, MemoryType
from devices.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

entries = [
    Memory(
        id="NB_CLAUDE_ARCHITECTURE_ROLE",
        narrative=(
            "Claude is a peer employer of Igor alongside Akien and Leah. "
            "Claude's role: Designer (architecture + conversation) and dev collaborator. "
            "Claude does not own Igor's state — it queries Igor's graph via the notebook "
            "and CC bridge to stay oriented across session resets. "
            "When Claude's context resets, Igor's graph holds what Claude learned. "
            "This notebook is how Claude reads it back."
        ),
        memory_type=MemoryType.FACTUAL,
        parent_id="CP2",
        metadata={
            "employer_id": "claude",
            "notebook_key": "architecture_role",
            "source": "seed",
        },
    ),
    Memory(
        id="NB_CLAUDE_INERTIA_TABLE",
        narrative=(
            "Inertia levels for Igor source files: "
            "HIGH (0.90+) = brainstem/, memory/models.py, cognition/reasoners/base.py — never edit casually. "
            "MEDIUM = cognition/, memory/cortex.py, anthropic.py, main.py — discuss before editing. "
            "LOW = tools/, dashboard/, thalamus.py, cognition/word_graph.py — freely improvable. "
            "Always read a file before editing. Always get plan approval before execution."
        ),
        memory_type=MemoryType.FACTUAL,
        parent_id="CP2",
        metadata={
            "employer_id": "claude",
            "notebook_key": "inertia_table",
            "source": "seed",
        },
    ),
    Memory(
        id="NB_CLAUDE_OPEN_DESIGN_THREADS",
        narrative=(
            "Open design threads as of 2026-03-15: "
            "(1) Employer model prototype (#239) — metadata.employer_id convention + cortex.for_employer() + /api/cc_notebook endpoint. "
            "(2) NE TraversalCursor (#236) — implemented; cursor tracks thread_topic across NE cycles; oscillation detection wired. "
            "(3) Traversal DSL (#237) — deferred until debugging pain demands it. "
            "(4) Decision capture habit (#235) — seeded PROC_DECISION_CAPTURE + PROC_DECISION_CAPTURE_CC. "
            "(5) Three-session CC pattern (#234) — Designer + Long Worker + Short Worker."
        ),
        memory_type=MemoryType.FACTUAL,
        parent_id="CP2",
        metadata={
            "employer_id": "claude",
            "notebook_key": "open_design_threads",
            "source": "seed",
        },
    ),
    Memory(
        id="NB_CLAUDE_CC_BRIDGE",
        narrative=(
            "Claude Code → Igor channel: POST http://localhost:8080/api/cc_send with {content: '...'}. "
            "Author injected as 'claude-code'. "
            "Igor notebook: GET /api/cc_notebook?employer=claude returns Claude's entries. "
            "POST /api/cc_notebook adds or updates an entry: {employer, key, content, parent_id}."
        ),
        memory_type=MemoryType.FACTUAL,
        parent_id="CP4",
        metadata={
            "employer_id": "claude",
            "notebook_key": "cc_bridge",
            "source": "seed",
        },
    ),
]

for entry in entries:
    existing = cortex.get(entry.id)
    if existing:
        cortex.store(entry)
        print(f"  updated: {entry.id}")
    else:
        cortex.store(entry)
        print(f"  seeded:  {entry.id}")

print("Done.")
