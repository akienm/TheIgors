"""
seed_navigational_heuristics.py — G51: Akien's domain-independent question patterns.

These are the navigational heuristics Akien applies automatically across any domain.
They are his executive function fingerprint — the questions he reaches for before
he knows he's reaching for them.

Seeded as INTERPRETIVE memories (not PROCEDURAL) because they are meaning-making
schemas, not action procedures. They shape how situations get interpreted and which
branches of the tree get explored next.

They are also seeded as Igor's heuristics — Igor should know to apply them and
surface them when they are relevant to whatever Akien is working on.

Run from repo root:
  python claudecode/seed_navigational_heuristics.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"))

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

heuristics = [
    Memory(
        id="PROC_HEURISTIC_HOW_MUST",
        narrative=(
            "The most powerful design question is: How must this work? "
            "Not 'how could this work' or 'what might work' — but what the problem structure "
            "REQUIRES. This derives from necessity, not possibility. "
            "It eliminates options before they're built. It is the upstream eliminator. "
            "When Akien asks this question, or when I am designing anything, "
            "this is the question that should come first."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "how must this work design requirement constraint derive upstream eliminate",
            "heuristic_type": "design_constraint",
            "applies_when": "designing any system, choosing between approaches",
            "why": (
                "G51: Akien's chief design heuristic. Constrains before building. "
                "Session 2026-03-11."
            ),
            "inertia": 0.40,
        },
    ),

    Memory(
        id="PROC_HEURISTIC_FIRST_RESPONSE",
        narrative=(
            "When facing any situation or choice, Akien's first introspection tool is: "
            "What's the first thing I say or do in response to that? "
            "This is a direct query of the interpretive layer — it simulates output "
            "before committing to it. It reveals which branch of the tree activates first. "
            "I should apply this when helping Akien think through responses or reactions. "
            "The first answer is data about what's already wired, not necessarily what's best."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "first thing say respond reaction response introspect interpret",
            "heuristic_type": "introspection",
            "applies_when": "navigating responses, reactions, choices",
            "why": "G51: Chief introspection tool. Direct query of interpretive layer.",
            "inertia": 0.35,
        },
    ),

    Memory(
        id="PROC_HEURISTIC_ALIGNMENT",
        narrative=(
            "When choosing between options, ask: which choice is most in alignment "
            "with who I'd most like to be? "
            "This question prunes by identity, not by logic or convenience. "
            "It is a values attractor — it weights the decision tree toward character. "
            "I should surface this when Akien is weighing options and the stakes involve "
            "who he is, not just what gets done."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "alignment values identity choice who i want to be character best version",
            "heuristic_type": "values_filter",
            "applies_when": "choosing between options where character is at stake",
            "why": "G51: Identity-weighted pruning. Not logic, not convenience — character.",
            "inertia": 0.45,
        },
    ),

    Memory(
        id="PROC_HEURISTIC_FITS_HERE",
        narrative=(
            "When there is a gap in a design, a conversation, or a plan, ask: "
            "What looks like it would fit there? "
            "This is pattern completion — you've seen the shape of the gap, "
            "now search for the matching piece. "
            "It works across domains: missing code, missing concept, missing word, "
            "missing person for a role. The gap shape is the search query."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "gap missing fit design pattern complete what goes here",
            "heuristic_type": "pattern_completion",
            "applies_when": "design gaps, missing pieces, incomplete structures",
            "why": "G51: Gap shape as search query. Cross-domain pattern matching.",
            "inertia": 0.30,
        },
    ),

    Memory(
        id="PROC_HEURISTIC_WORKAROUND",
        narrative=(
            "When a path is blocked, ask: how could we get around that? "
            "This is obstacle navigation — it fires when a branch is blocked "
            "and switches to lateral search. "
            "The question does not accept the obstacle as final. "
            "It looks for the adjacent path, the reframe, the approach from a different angle. "
            "I should apply this whenever a direct approach hits a wall."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "blocked obstacle workaround around alternative reframe constraint",
            "heuristic_type": "obstacle_navigation",
            "applies_when": "when direct path is blocked; when constraints feel final",
            "why": "G51: Lateral search trigger. Blocked branch → find adjacent path.",
            "inertia": 0.30,
        },
    ),

    Memory(
        id="PROC_HEURISTIC_LEVER",
        narrative=(
            "When facing a complex system or a hard problem, ask: where is the lever? "
            "This is the leverage point scan — looking for the place where small force "
            "produces large movement. "
            "Not all points of intervention are equal. The lever is the one where "
            "effort is minimized and effect is maximized. "
            "I should surface this when Akien is deciding where to focus effort."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "lever leverage where focus effort effect impact high yield minimum force",
            "heuristic_type": "leverage_scan",
            "applies_when": "allocating effort; choosing where to intervene in a complex system",
            "why": "G51: Systemic thinking. Find minimum force / maximum effect point.",
            "inertia": 0.35,
        },
    ),

    Memory(
        id="PROC_HEURISTIC_MONKEY_PROOF",
        narrative=(
            "When designing something other people will use, ask: "
            "how will us monkeys screw that up such that I get support questions? "
            "This is failure mode simulation — it models degraded human execution "
            "before committing to a design. "
            "People will misread, skip steps, assume wrong things, use the wrong input. "
            "Design for the monkey first. The expert case will take care of itself. "
            "I should apply this whenever we are building something for others."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "trigger": "design for others user error failure mode support questions humans misuse",
            "heuristic_type": "failure_simulation",
            "applies_when": "designing tools, processes, systems for other humans to use",
            "why": "G51: Human-use failure prediction. Design for degraded execution first.",
            "inertia": 0.30,
        },
    ),
]

for h in heuristics:
    existing = cortex.get(h.id)
    if existing:
        print(f"  [skip] {h.id} already exists")
        continue
    cortex.store(h)
    cortex.add_child("CP1", h.id)
    print(f"  [seeded] {h.id}  (interpretive heuristic) → parent=CP1")

print(f"\nDone. {len(heuristics)} heuristics processed.")
