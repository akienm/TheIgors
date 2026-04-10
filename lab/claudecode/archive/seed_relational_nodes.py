"""
seed_relational_nodes.py — #180: Investment weights.

Seeds the relational/investment nodes for people, projects, and ideas
that Akien has significant investment in. These are INTERPRETIVE memories
with metadata.source="relational" and an investment_weight.

When input mentions one of these nodes, it gets pre-attentively injected
into TWM as high-salience context before any traversal begins.

This is the "Leah at home lights up more than Krissy in Scotland" mechanism:
same love, different proximity coefficient → different activation threshold.

Run from repo root:
  python claudecode/seed_relational_nodes.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"))

from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

nodes = [
    # ── People ───────────────────────────────────────────────────────────────
    dict(
        name="Leah",
        narrative=(
            "Leah — Akien's partner, lives at home with him. "
            "High proximity, high investment. Akien's primary relationship. "
            "Watching for: anything that would help make her life suck less (CP4)."
        ),
        relationship_type="partner",
        investment_weight=0.95,
        proximity="present",
        valence=0.95,
    ),
    dict(
        name="Krissy",
        narrative=(
            "Krissy — Akien's girlfriend, lives in Scotland. "
            "Real attachment, lower activation due to geographic distance. "
            "Watching for: opportunities to connect, things she'd care about."
        ),
        relationship_type="partner",
        investment_weight=0.85,
        proximity="remote",
        valence=0.90,
    ),

    # ── Projects ─────────────────────────────────────────────────────────────
    dict(
        name="TheIgors",
        narrative=(
            "TheIgors project — building Igor, the persistent AI agent. "
            "Currently in NRE-adjacent phase for Akien: high salience, everything feels relevant. "
            "Core mission: inference-free cognition, the graph IS the thinker. "
            "Investment: Akien's primary technical and intellectual work."
        ),
        relationship_type="project",
        investment_weight=0.90,
        proximity="present",
        valence=0.90,
        extra_metadata={"nre_phase": True},
    ),
    dict(
        name="The Book",
        narrative=(
            "Akien's book project — a letter from him to a much younger version of himself. "
            "Igor's role: help surface gems from accumulated writings (Confluence + wiki). "
            "Investment: deeply personal, connected to Akien's life story and ADD experience."
        ),
        relationship_type="project",
        investment_weight=0.75,
        proximity="present",
        valence=0.85,
    ),

    # ── Ideas ─────────────────────────────────────────────────────────────────
    dict(
        name="The Architecture",
        narrative=(
            "The multilayer graph / inference engine architecture. "
            "Parsing and reasoning as unified tree traversal. "
            "The graph is the thinker; LLMs are graph trainers. "
            "Investment: the intellectual backbone of everything Akien and Igor are building."
        ),
        relationship_type="idea",
        investment_weight=0.85,
        proximity="present",
        valence=0.90,
    ),
    dict(
        name="ADD",
        narrative=(
            "Akien's ADD — Attention Deficit Disorder. "
            "Shapes how he works, learns, and relates. "
            "Claude Code enables his ADD brain to build things he could only dream before. "
            "Watching for: friction points, compensation strategies, design implications."
        ),
        relationship_type="idea",
        investment_weight=0.70,
        proximity="present",
        valence=0.65,
    ),
]


added = 0
skipped = 0
for node in nodes:
    node_id = f"REL_{node['name'].upper().replace(' ', '_')}"
    # Check if already exists
    existing = cortex.get(node_id)
    if existing:
        print(f"  [skip] {node_id} already exists")
        skipped += 1
        continue
    try:
        mem = cortex.store_relational(**node)
        print(
            f"  [stored] {mem.id}  "
            f"w={node['investment_weight']:.2f}  "
            f"prox={node['proximity']}  "
            f"{node['narrative'][:60]}..."
        )
        added += 1
    except Exception as e:
        print(f"  [error] {node_id}: {e}")
        skipped += 1

print(f"\nDone. {added} relational nodes stored, {skipped} skipped.")
print("Investment weight pre-check will now activate on input mentioning these nodes.")
