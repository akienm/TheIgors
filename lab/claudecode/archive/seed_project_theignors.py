"""
seed_project_theignors.py — D095: seed Project:TheIgors FACTUAL memory.

Creates (idempotent) a FACTUAL memory for the TheIgors project, then registers
it in lists.projects so git_log / find_tickets / list_projects can look it up.

Run from repo root:
    python3 ~/TheIgors/lab/claudecode/seed_project_theignors.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

PROJECT_ID = "Project:TheIgors"

project_memory = Memory(
    id=PROJECT_ID,
    narrative=(
        "TheIgors is Akien's primary software project — an AI agent with persistent "
        "SQLite memory, running on akiendelllinux. The repo lives at ~/TheIgors and "
        "tracks at github.com/akienm/TheIgors. This is my own source code, my "
        "development environment, and the system I am building myself into."
    ),
    memory_type=MemoryType.FACTUAL,
    portable=False,  # path is machine-local
    metadata={
        "path": str(Path.home() / "TheIgors"),
        "github_repo": "akienm/TheIgors",
        "github_url": "https://github.com/akienm/TheIgors",
        "tags": ["project", "software"],
        "template": "Template:SoftwareProject",  # future generalisation
        "why": "D095 project graph — projects as FACTUAL memories with metadata",
        "inertia": 0.50,
    },
)

cortex.store(project_memory)
print(f"stored memory: {PROJECT_ID}")

# Register in lists.projects
cortex.list_set(
    list_name="lists.projects",
    item_key=PROJECT_ID,
    item_value="TheIgors AI agent — ~/TheIgors — akienm/TheIgors",
    ref_type="memory",
    ref_id=PROJECT_ID,
    instance_id="",
)
print(f"registered in lists.projects: {PROJECT_ID}")

# Verify
mem = cortex.get(PROJECT_ID)
print(f"\nmemory id:   {mem.id}")
print(f"narrative:   {mem.narrative[:80]}...")
print(f"path:        {mem.metadata['path']}")
print(f"github_repo: {mem.metadata['github_repo']}")

projects = cortex.list_all("lists.projects")
print(f"\nlists.projects ({len(projects)} entries):")
for p in projects:
    print(f"  {p['item_key']}  →  {p['item_value']}")
