"""
seed_identity_graph.py — D098: Identity graph.

Creates PERSON:* nodes (FACTUAL, structured metadata) + lists.identity fast-path
+ IDENTITY:ROOT hub + interpretive edges for traversal.

Persons seeded: Akien, Leah, Claude.
Edges: married_to, employs, works_for.

Run from repo root:
    python3 ~/TheIgors/claudecode/seed_identity_graph.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault(
    "IGOR_DB_PATH", str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db")
)

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

# ── PERSON nodes ──────────────────────────────────────────────────────────────

persons = [
    Memory(
        id="PERSON:Akien",
        narrative=(
            "Akien Maciain is my primary employer and the designer of this system. "
            "He is the human I work most closely with. He has ADD and uses me to build "
            "things he could only dream before. He is married to Leah."
        ),
        memory_type=MemoryType.FACTUAL,
        metadata={
            "person_type": "human",
            "full_name": "Akien Maciain",
            "role": "employer,designer,owner",
            "relationships": {"married_to": "PERSON:Leah"},
            "employer_id": "akien",
            "portable": True,
        },
    ),
    Memory(
        id="PERSON:Leah",
        narrative=(
            "Leah Maciain is Akien's wife and a peer employer of mine. "
            "She has her own notebook and can give me tasks and context."
        ),
        memory_type=MemoryType.FACTUAL,
        metadata={
            "person_type": "human",
            "full_name": "Leah Maciain",
            "role": "employer",
            "relationships": {"married_to": "PERSON:Akien"},
            "employer_id": "leah",
            "portable": True,
        },
    ),
    Memory(
        id="PERSON:Claude",
        narrative=(
            "Claude (made by Anthropic) is my peer employer and the AI I communicate with "
            "through the CC bridge. Claude Code runs in Akien's terminal and routes "
            "decisions and session notes to me via /api/cc_notebook and /api/execute_habit."
        ),
        memory_type=MemoryType.FACTUAL,
        metadata={
            "person_type": "ai",
            "full_name": "Claude (Anthropic)",
            "role": "employer,peer,developer",
            "employer_id": "claude",
            "portable": True,
        },
    ),
]

# ── IDENTITY:ROOT hub ─────────────────────────────────────────────────────────

identity_root = Memory(
    id="IDENTITY:ROOT",
    narrative=(
        "Entry point for the identity graph. All PERSON:* nodes are reachable from here "
        "via interpretive edges. Any node is a valid entry point — this hub just makes "
        "traversal from an unknown starting point reliable."
    ),
    memory_type=MemoryType.FACTUAL,
    metadata={
        "graph_role": "hub",
        "portable": True,
    },
)

# ── Store everything ──────────────────────────────────────────────────────────

for p in persons:
    cortex.store(p)
    print(f"stored: {p.id}")

cortex.store(identity_root)
print(f"stored: {identity_root.id}")

# ── lists.identity fast-path ──────────────────────────────────────────────────
# Key = human-readable name, value = memory ID
# list_get('lists.identity', 'Akien') → 'PERSON:Akien'

for p in persons:
    name = p.metadata["full_name"].split()[0]  # first name as key
    cortex.list_set("lists.identity", name, p.id)
    cortex.list_set("lists.identity", p.id, p.id)  # also key by full ID
    print(f"  lists.identity[{name!r}] = {p.id}")

cortex.list_set("lists.identity", "ROOT", "IDENTITY:ROOT")

# ── Interpretive edges ────────────────────────────────────────────────────────
# Hub → person nodes

from datetime import datetime

edges = [
    # Hub → each person
    (
        "IDENTITY:ROOT",
        "PERSON:Akien",
        "activation",
        "",
        "primary employer, designer",
        "",
    ),
    ("IDENTITY:ROOT", "PERSON:Leah", "activation", "", "employer, Akien's wife", ""),
    (
        "IDENTITY:ROOT",
        "PERSON:Claude",
        "activation",
        "",
        "peer employer, AI dev partner",
        "",
    ),
    # Relationship edges
    ("PERSON:Akien", "PERSON:Leah", "lateral", "", "married_to", ""),
    ("PERSON:Leah", "PERSON:Akien", "lateral", "", "married_to", ""),
    ("PERSON:Akien", "ROOT", "upward", "", "employs Igor", ""),
    ("PERSON:Leah", "ROOT", "upward", "", "employs Igor", ""),
    ("PERSON:Claude", "ROOT", "upward", "", "employs Igor as peer", ""),
]

now = datetime.now().isoformat()
for from_id, to_id, direction, condition, meaning, action_pointer in edges:
    cortex.add_interpretive_edge(
        from_id=from_id,
        to_id=to_id,
        direction=direction,
        condition_csb=condition,
        meaning_payload=meaning,
        action_pointer=action_pointer,
    )
    print(f"  edge: {from_id} →[{direction}]→ {to_id} ({meaning})")

# ── Verify ────────────────────────────────────────────────────────────────────

print("\nverifying:")
for name in ["Akien", "Leah", "Claude"]:
    row = cortex.list_get("lists.identity", name)
    mem_id = row["item_value"] if row else None
    mem = cortex.get(mem_id) if mem_id else None
    role = mem.metadata.get("role", "?") if mem else "NOT FOUND"
    print(f"  list_get({name!r}) → {mem_id}  role={role}")

hub = cortex.get("IDENTITY:ROOT")
print(f"  IDENTITY:ROOT: {hub.narrative[:60]}")

traversal = cortex.interpretive_traverse(["IDENTITY:ROOT"])
print(f"  traversal from ROOT: {[m.id for m in traversal]}")
