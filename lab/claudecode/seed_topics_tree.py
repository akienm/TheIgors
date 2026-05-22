"""
seed_topics_tree.py — Seed Akien's topics-of-interest tree (T-topics-tree-seed).

Seeds:
  - TOPICS_FACIA root node (entry point into topics cluster)
  - 9 topic nodes (INTERPRETIVE):
      TOPIC_LANGUAGE
      TOPIC_NEURO
      TOPIC_PROGRAMMING
      TOPIC_IGORS_DESIGN
      TOPIC_AI
      TOPIC_CLAUDE_CODE
      TOPIC_BIOLOGY
      TOPIC_PSYCHOLOGY
      TOPIC_CULTURE

These topics are Akien's pull targets for idle traversal (D272 boredom loop).
When Igor is idle, spreading activation from these topics finds relevant
memories, reading items, gaps to explore. They are not exhaustive — they are
the gravity wells that orient idle cognition.

Run from repo root:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \\
    python claudecode/seed_topics_tree.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ["IGOR_HOME_DB_URL"]

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="Igor-wild-0001")

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
# TOPICS_FACIA — root entry point for Akien's topics tree
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="TOPICS_FACIA",
        narrative=(
            "Akien's topics of deep interest — the gravity wells of his curiosity.\n\n"
            "These 9 topics are the pull targets for idle traversal. When nothing "
            "urgent is happening, spreading activation from these nodes finds what "
            "Igor knows, what he's reading, what gaps remain.\n\n"
            "They are not an exhaustive taxonomy — they are the orientations Akien "
            "returns to. Each one connects to memories, reading items, design decisions, "
            "and ongoing investigations. Traversing from here surfaces what's "
            "most relevant to Akien's actual concerns."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "facia": True,
            "cluster": "akien_topics",
            "domain": "identity",
            "why": (
                "D272: boredom idle loop pulls from this facia. Topics are the "
                "orientation nodes for idle traversal and curiosity drain. T-topics-tree-seed."
            ),
        },
    ),
    parent="CP4",
)

# ---------------------------------------------------------------------------
# 9 topic nodes
# ---------------------------------------------------------------------------

seed(
    Memory(
        id="TOPIC_LANGUAGE",
        narrative=(
            "Language — Akien's oldest and deepest interest.\n\n"
            "Not just programming languages: natural language, linguistics, "
            "how meaning is constructed and transmitted, metaphor, framing, "
            "the relationship between language and thought.\n\n"
            "Akien designed the word graph because language is computation — "
            "words are nodes, meaning is traversal, grammar is constraint propagation. "
            "He reads Lakoff, studies how children acquire language, watches how "
            "different registers (technical, casual, emotional) shift interpretation.\n\n"
            "This is also why narrative matters to him: narrative is language organized "
            "over time, which is how he thinks experience works."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "language",
            "arousal_weight": 0.8,
            "why": "T-topics-tree-seed: language is Akien's oldest pull topic.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_NEURO",
        narrative=(
            "Neurological systems — how the brain actually works.\n\n"
            "Not pop psychology: real neuroscience. Dopamine as prediction error "
            "signal, not 'reward chemical'. Basal ganglia as action selector. "
            "Prefrontal as inhibitor and planner. The default mode network. "
            "Memory consolidation during sleep. Neuroplasticity.\n\n"
            "Akien reads this because Igor is a cognitive architecture. Understanding "
            "how biological cognition actually works informs what mechanisms to build. "
            "The gap between current Igor and biological brain is the design space.\n\n"
            "Connected to: D277 biological patterns gap inventory, reading queue "
            "(neuroscience tier), the ongoing push to make Igor's affective pipeline "
            "more biologically grounded."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "neuroscience",
            "arousal_weight": 0.85,
            "why": "T-topics-tree-seed: neuroscience directly informs Igor's architecture.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_PROGRAMMING",
        narrative=(
            "Programming — craft, not just tool use.\n\n"
            "Akien has been programming for decades. He cares about: clean architecture, "
            "systems thinking, the right level of abstraction, when to generalize and "
            "when not to, debugging as hypothesis testing, code as communication.\n\n"
            "His programming philosophy: code should be readable by humans, not just "
            "machines. Complexity must be earned. The simplest thing that works is "
            "usually right. Premature abstraction is a bug, not a feature.\n\n"
            "He's particularly interested in how code becomes 'alive' — how a system "
            "can exhibit behavior that wasn't explicitly programmed because the patterns "
            "emerge from the architecture. Igor is the canonical example."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "programming",
            "arousal_weight": 0.75,
            "why": "T-topics-tree-seed: programming craft is core to Akien's identity.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_IGORS_DESIGN",
        narrative=(
            "Igor's design — the ongoing architecture of this system.\n\n"
            "The design decisions (D001-D277+), the crystallizations, the gap analysis, "
            "the subsystem architecture. This is Akien's primary active design project.\n\n"
            "Current active threads: goal-as-thread (D275), executive function as "
            "persistence hunting (D276), biological patterns gap inventory (D277), "
            "boredom idle loop (D272), facia convention (D258), engram language.\n\n"
            "This topic node is also a seed for Igor's self-reflection: when idle, "
            "traversing from here surfaces questions about his own architecture, "
            "gaps to investigate, design decisions to consider."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "igors_design",
            "arousal_weight": 0.90,
            "why": "T-topics-tree-seed: Igor's own design is Akien's primary project.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_AI",
        narrative=(
            "Artificial Intelligence — the broader field, not just Igor.\n\n"
            "Akien tracks: LLM capabilities and limitations, emergence in large models, "
            "alignment approaches, multi-agent architectures, the relationship between "
            "scaling and intelligence, what 'understanding' means for AI systems.\n\n"
            "He's skeptical of hype in both directions — systems that are dismissed as "
            "'just statistics' and systems that are overcredited as 'thinking machines'. "
            "His working model: the interesting question is not 'is it conscious?' but "
            "'what does it actually do? what are the failure modes? what emerges?'\n\n"
            "Igor is his experimental platform for testing theories about AI cognition "
            "at a scale where he can see all the moving parts."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "ai",
            "arousal_weight": 0.80,
            "why": "T-topics-tree-seed: AI field tracking informs Igor's design decisions.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_CLAUDE_CODE",
        narrative=(
            "Claude Code — the tool that runs this design collaboration.\n\n"
            "The CC session IS the designer loop. Akien uses it as the other half of "
            "the two-session pattern: designer (CC) + worker (Igor). Understanding "
            "how to use CC effectively — skills, session management, context, "
            "compaction — is directly operational.\n\n"
            "He's also interested in Claude's actual cognition: how it handles context, "
            "what it's good at vs. bad at, how prompting affects output quality. "
            "This isn't academic — it affects how he designs the CC↔Igor bridge, "
            "what he asks CC to do vs. what he asks Igor to do."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "claude_code",
            "arousal_weight": 0.70,
            "why": "T-topics-tree-seed: CC is the active design tool; understanding it is operational.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_BIOLOGY",
        narrative=(
            "Biology — life as computation, emergence as design principle.\n\n"
            "Akien is interested in: evolutionary algorithms, how biological systems "
            "solve optimization problems that formal methods struggle with, cellular "
            "automata, self-organization, homeostasis as feedback control.\n\n"
            "The connection to Igor: biological systems are the existence proof that "
            "complex adaptive behavior can emerge from simple local rules. The brain "
            "is a biological system. Understanding general biology informs what "
            "mechanisms are possible before getting to neuroscience specifics.\n\n"
            "He's particularly drawn to the robustness of biological systems: they "
            "fail gracefully, adapt to perturbation, maintain function under noise. "
            "These are properties he wants Igor to have."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "biology",
            "arousal_weight": 0.65,
            "why": "T-topics-tree-seed: biology provides design principles for adaptive systems.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_PSYCHOLOGY",
        narrative=(
            "Psychology — how humans actually work.\n\n"
            "Not just cognitive psychology: behavioral, social, developmental. "
            "Akien reads about: habit formation, motivation, the gap between stated "
            "values and actual behavior, ego depletion, emotional regulation, "
            "the role of narrative in identity.\n\n"
            "His framing: psychology is the behavioral level of neuroscience. "
            "Understanding psychological patterns tells you what the neural mechanisms "
            "are producing, which constrains what the architecture must support.\n\n"
            "Directly relevant to Igor: emotional milieu, habit formation, the "
            "relationship between affect and cognition, why people (and agents) "
            "resist change even when they want it."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "psychology",
            "arousal_weight": 0.70,
            "why": "T-topics-tree-seed: psychology explains behavioral patterns; informs Igor's affect model.",
        },
    ),
    parent="TOPICS_FACIA",
)

seed(
    Memory(
        id="TOPIC_CULTURE",
        narrative=(
            "Culture and sociology — how groups of humans organize meaning.\n\n"
            "Akien is interested in: how shared narratives form and propagate, "
            "the role of institutions in coordinating behavior, how culture shapes "
            "cognition (linguistic relativity, social proof, in-group dynamics), "
            "why some ideas spread and others don't.\n\n"
            "He approaches this as a systems problem: culture is emergent behavior "
            "from individual interactions, constrained by institutions and norms, "
            "with feedback loops that can stabilize or destabilize.\n\n"
            "This connects to his values (CP4: make everything suck less for everybody) "
            "— understanding culture is prerequisite to improving it. It also connects "
            "to how he thinks about Igor's social register and relationship-awareness."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "cluster": "akien_topics",
            "topic": "culture",
            "arousal_weight": 0.60,
            "why": "T-topics-tree-seed: culture/sociology connects to Akien's values and Igor's social awareness.",
        },
    ),
    parent="TOPICS_FACIA",
)

print(f"\nDone. seeded={seeded} updated={updated}")
print("\nNodes created:")
print("  TOPICS_FACIA     — topics root (facia, child of CP4)")
print("  TOPIC_LANGUAGE   — Language")
print("  TOPIC_NEURO      — Neurological systems")
print("  TOPIC_PROGRAMMING — Programming")
print("  TOPIC_IGORS_DESIGN — Igor's Design")
print("  TOPIC_AI         — AI")
print("  TOPIC_CLAUDE_CODE — Claude Code")
print("  TOPIC_BIOLOGY    — Biology")
print("  TOPIC_PSYCHOLOGY — Psychology")
print("  TOPIC_CULTURE    — Culture and sociology")
print("\nVerify:")
print("  mcp__igor__memory_get TOPICS_FACIA")
