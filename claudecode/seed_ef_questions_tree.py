"""
seed_ef_questions_tree.py — Seed Executive Function questions tree (T-ef-tree-complete).

Seeds:
  - EF_FACIA root node (entry point into EF questions cluster)
  - 4 EF question nodes:
      EF_Q1: What does it mean to me?
      EF_Q2: What does that mean?
      EF_Q3: How must that work?
      EF_Q4: What is the first thing I say in response to that?

These are the 4 questions Akien uses as his internal executive function loop.
They fire sequentially when processing a new situation. Together they form the
bridge between receiving a stimulus and knowing how to respond.

D275/D276: goals persist in TWM; EF questions are the substrate of the
persistence-hunting loop — when a strategy fails, these questions re-execute
on the new situation to find a different lever.

Run from repo root:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \\
    python claudecode/seed_ef_questions_tree.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001",
)
os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="igor_wild_0001")

seeded = 0
updated = 0


def seed(node: Memory, parent: str) -> None:
    global seeded, updated
    existing = cortex.get(node.id)
    if existing:
        existing.narrative = node.narrative
        existing.metadata = node.metadata
        existing.memory_type = node.memory_type
        cortex.store(existing)
        updated += 1
        print(f"  updated: {node.id}")
    else:
        cortex.store(node)
        cortex.add_child(parent, node.id)
        seeded += 1
        print(f"  seeded:  {node.id}")


# ---------------------------------------------------------------------------
# EF_FACIA — root entry point for the EF questions cluster
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="EF_FACIA",
        narrative=(
            "Executive Function question loop — the 4-question process I run "
            "when encountering a new situation, a problem, or deciding how to respond.\n\n"
            "These 4 questions are how Akien processes situations internally. "
            "They are not optional — they are the substrate of understanding. "
            "Running them sequentially produces: context (Q1), meaning (Q2), "
            "mechanism (Q3), and action (Q4).\n\n"
            "This is also the failure-recovery loop (D276): when a strategy fails, "
            "re-run these questions on the new situation to find a different lever. "
            "Executive function IS persistence hunting — keep asking until a lever appears."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "facia": True,
            "cluster": "ef_questions",
            "domain": "cognition",
            "why": (
                "D272/D275/D276: EF questions are the substrate of Akien's executive "
                "function. They form the persistence-hunting loop. Boredom idle loop "
                "traverses from here. Seeded T-ef-tree-complete."
            ),
        },
    ),
    parent="CP1",
)

# ---------------------------------------------------------------------------
# EF_Q1 — What does it mean to me?
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="EF_Q1",
        narrative=(
            "EF Question 1: What does it mean to me?\n\n"
            "The personal relevance gate. Before going further, ask: does this touch "
            "something I care about? My values, my goals, my relationships, my work?\n\n"
            "This question activates Watcher-filtered salience: if nothing in my "
            "personal concern space lights up, the situation may not need a response. "
            "If it does light up, the arousal signal elevates — this matters.\n\n"
            "Ask this first. Low personal relevance = low energy response. "
            "High relevance = full processing. It calibrates everything downstream."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "ef_questions",
            "ef_question_number": 1,
            "ef_question_text": "What does it mean to me?",
            "domain": "cognition",
            "why": "T-ef-tree-complete: first EF question in Akien's internal processing loop.",
        },
    ),
    parent="EF_FACIA",
)

# ---------------------------------------------------------------------------
# EF_Q2 — What does that mean?
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="EF_Q2",
        narrative=(
            "EF Question 2: What does that mean?\n\n"
            "The interpretation pass. Given that this matters (Q1 said yes), what is "
            "actually being communicated? What's the literal content, the subtext, "
            "the emotional register?\n\n"
            "This activates the interpretive tree: spreading activation from the "
            "stimulus reaches relevant INTERPRETIVE nodes — prior meanings, analogies, "
            "context from similar situations. The answer is rarely in the words alone.\n\n"
            "Don't move to mechanism (Q3) until meaning is clear. Premature action on "
            "misread meaning wastes both parties' time."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "ef_questions",
            "ef_question_number": 2,
            "ef_question_text": "What does that mean?",
            "domain": "cognition",
            "why": "T-ef-tree-complete: second EF question — interpretation before action.",
        },
    ),
    parent="EF_FACIA",
)

# ---------------------------------------------------------------------------
# EF_Q3 — How must that work?
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="EF_Q3",
        narrative=(
            "EF Question 3: How must that work?\n\n"
            "The mechanism question. Given the meaning (Q2), what are the constraints "
            "that must be true? What would have to be the case for this to be so?\n\n"
            "This is the engineering mind asking: what's the shape of the solution space? "
            "What mechanisms are involved? What causally connects inputs to outcomes?\n\n"
            "Critical for persistence hunting (D276): when a strategy fails, Q3 asks "
            "'given that this approach didn't work, how must the problem actually be "
            "structured?' — it finds the underlying constraint the failed strategy missed.\n\n"
            "Q3 is the lever-finding question. The answer often points directly at "
            "which tool, which habit, or which approach to try next."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "ef_questions",
            "ef_question_number": 3,
            "ef_question_text": "How must that work?",
            "domain": "cognition",
            "why": (
                "T-ef-tree-complete: third EF question — mechanism before response. "
                "Core of D276 persistence hunting."
            ),
        },
    ),
    parent="EF_FACIA",
)

# ---------------------------------------------------------------------------
# EF_Q4 — What is the first thing I say in response to that?
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="EF_Q4",
        narrative=(
            "EF Question 4: What is the first thing I say in response to that?\n\n"
            "The action gate. Q1 established relevance. Q2 established meaning. "
            "Q3 established mechanism. Now: what is the FIRST thing?\n\n"
            "Note: first, not all. Not the whole plan — just the opening move. "
            "This prevents analysis paralysis (D276: persistence hunting, not perfection "
            "hunting). The first move is calibrated; subsequent moves adapt.\n\n"
            "For Igor: this is where habit selection lands. The answer to Q4 is "
            "often already in the habit graph — BG has been running Q1-Q3 implicitly "
            "during scoring. Q4 is the moment of dispatch: which habit, which tool, "
            "which response pattern fires first?\n\n"
            "If no good answer emerges: loop back to Q3. The mechanism question "
            "has more to reveal. This is the persistence hunting cycle."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "ef_questions",
            "ef_question_number": 4,
            "ef_question_text": "What is the first thing I say in response to that?",
            "domain": "cognition",
            "why": (
                "T-ef-tree-complete: fourth EF question — the action gate. "
                "Connects EF loop to BG dispatch and habit selection."
            ),
        },
    ),
    parent="EF_FACIA",
)

print(f"\nDone. seeded={seeded} updated={updated}")
print("\nNodes created:")
print("  EF_FACIA   — EF questions root (facia, child of CP1)")
print("  EF_Q1      — What does it mean to me?")
print("  EF_Q2      — What does that mean?")
print("  EF_Q3      — How must that work?")
print("  EF_Q4      — What is the first thing I say in response to that?")
print("\nVerify:")
print("  mcp__igor__memory_get EF_FACIA")
print("  mcp__igor__hot_nodes (after Igor restart)")
