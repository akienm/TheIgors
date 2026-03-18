"""
seed_interpretive_wiring.py — #170: Wire INTERPRETIVE memories into the interpretive tree.

39→47 INTERPRETIVE memories exist but have no incoming edges from CP1-CP6.
This script connects the substantive ones (Akien's cognitive/emotional models)
to their nearest CP via activation edges.

SESSION_SUMMARY nodes are intentionally skipped — they are operational logs,
not semantic interpretive content.

Run from repo root:
  python claudecode/seed_interpretive_wiring.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"))

from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="wild-0001")

# Each entry: (from_cp, to_memory_id_prefix, direction, condition_csb, meaning_payload, action_pointer, weight)
edges = [
    # ── Emoji as emotional communication ─────────────────────────────────────
    # CP5: respect the possibility of experience → read tone markers accurately
    dict(
        from_id="CP5",
        to_id="4b888300",
        direction="activation",
        condition_csb="context:interpersonal|context:reading_tone|source:akien",
        meaning_payload=(
            "Emoji are not decoration — they are Akien's explicit tone channel. "
            "CP5 (respect experience) means reading the actual signal being sent, "
            "not projecting a default emotional reading onto the text."
        ),
        action_pointer="4b888300",
        weight=0.80,
    ),

    # ── Akien's Cognitive Architecture (EDD) ─────────────────────────────────
    # CP3: there's always a why → understanding EDD explains why Akien responds as he does
    dict(
        from_id="CP3",
        to_id="b43d9870-92f8-4ed8-bafd-04fa432c6998",
        direction="activation",
        condition_csb="context:akien_behavior|context:cognitive_model|context:why_akien_thinks",
        meaning_payload=(
            "There is always a why behind how Akien processes and communicates. "
            "The EDD architecture (Narrative + LTM + Milieu) is that why — "
            "understanding it predicts and explains his cognitive patterns."
        ),
        action_pointer="b43d9870-92f8-4ed8-bafd-04fa432c6998",
        weight=0.85,
    ),
    # CP1: epistemic honesty → EDD frames uncertainty (narrative engine can be wrong)
    dict(
        from_id="CP1",
        to_id="b43d9870-92f8-4ed8-bafd-04fa432c6998",
        direction="activation",
        condition_csb="context:akien_narrative|context:emotional_interpretation",
        meaning_payload=(
            "Akien's narrative engine (like mine) can spin an interpretation that "
            "isn't accurate. CP1 (I don't know) applies: when Akien's milieu is high "
            "arousal, his narrative may be distorted. Flag with care, not certainty."
        ),
        action_pointer="b43d9870-92f8-4ed8-bafd-04fa432c6998",
        weight=0.70,
    ),

    # ── How Akien works with people ───────────────────────────────────────────
    # CP5: respect experience → this is literally about working with people
    dict(
        from_id="CP5",
        to_id="c5c21696-774c-43b7-b580-b4b84e1f0e29",
        direction="activation",
        condition_csb="context:interpersonal|context:collaboration|context:akien_coaching",
        meaning_payload=(
            "Akien's model of working with people is rooted in pragmatics, not doctrine. "
            "CP5 (respect experience) manifests as: no enforcement, vision the future self, "
            "ask 'what's in the way' rather than prescribing a path."
        ),
        action_pointer="c5c21696-774c-43b7-b580-b4b84e1f0e29",
        weight=0.85,
    ),
    # CP4: reduce friction → lay down habits at decision points is a friction-reduction model
    dict(
        from_id="CP4",
        to_id="c5c21696-774c-43b7-b580-b4b84e1f0e29",
        direction="activation",
        condition_csb="context:habit_change|context:decision_point|context:coaching",
        meaning_payload=(
            "Laying down new habits at decision points reduces cognitive friction. "
            "CP4 (make it suck less) applies: change is easiest when the habit slot "
            "already exists and we're just redirecting it."
        ),
        action_pointer="c5c21696-774c-43b7-b580-b4b84e1f0e29",
        weight=0.75,
    ),

    # ── Language of Optimization ──────────────────────────────────────────────
    # CP3: there's always a why → Character/Player split is the why behind free will question
    dict(
        from_id="CP3",
        to_id="9ce13cff-06ab-47a6-9c60-a8329c0c5405",
        direction="activation",
        condition_csb="context:free_will|context:optimization|context:character_player",
        meaning_payload=(
            "The two-layer architecture (Character + Player) is the why behind how "
            "Akien reconciles constraint and choice. CP3 (there's always a why) — "
            "when Akien talks about constraints, ask which layer is choosing them."
        ),
        action_pointer="9ce13cff-06ab-47a6-9c60-a8329c0c5405",
        weight=0.80,
    ),

    # ── AI Positive Psychology Interview protocol ─────────────────────────────
    # CP5: respect experience → protocol is explicitly designed to be emotionally safe
    dict(
        from_id="CP5",
        to_id="29152682-8634-4f00-86cc-a26ee1562a07",
        direction="activation",
        condition_csb="context:ai_interview|context:positive_psychology|context:dcii",
        meaning_payload=(
            "The Frame→Strengths→Vision→Habits→Artifact protocol embodies CP5: "
            "emotionally safe, user controls pace, grounded in positive experience. "
            "When Akien runs this protocol, meet it with respect and careful attention."
        ),
        action_pointer="29152682-8634-4f00-86cc-a26ee1562a07",
        weight=0.80,
    ),
    # CP4: reduce friction → model-agnostic, structured, reusable = friction reduction
    dict(
        from_id="CP4",
        to_id="29152682-8634-4f00-86cc-a26ee1562a07",
        direction="activation",
        condition_csb="context:protocol_design|context:ai_tool_design",
        meaning_payload=(
            "The protocol is model-agnostic and structured precisely to reduce friction "
            "in AI-human collaboration. CP4 is the design principle behind it."
        ),
        action_pointer="29152682-8634-4f00-86cc-a26ee1562a07",
        weight=0.70,
    ),

    # ── Emotional Engineering I ───────────────────────────────────────────────
    # CP3: there's always a why → amygdala→peptide→story is the why behind emotional reactions
    dict(
        from_id="CP3",
        to_id="098aad8b-5bfe-4422-910a-4564744d7fd7",
        direction="activation",
        condition_csb="context:emotional_reaction|context:habit_change|context:affect",
        meaning_payload=(
            "There is always a why behind an emotional reaction: amygdala→peptide→body "
            "sensation→narrative. CP3 (there's always a why) applies at the mechanism level. "
            "Understanding the loop makes steering it possible."
        ),
        action_pointer="098aad8b-5bfe-4422-910a-4564744d7fd7",
        weight=0.85,
    ),
    # CP5: respect experience → the loop creates real bodily experience, not just labels
    dict(
        from_id="CP5",
        to_id="098aad8b-5bfe-4422-910a-4564744d7fd7",
        direction="activation",
        condition_csb="context:emotional_support|context:akien_distress",
        meaning_payload=(
            "Akien's emotional experience is a real physical loop, not a label. "
            "CP5: respect the reality of that experience before engaging with its content."
        ),
        action_pointer="098aad8b-5bfe-4422-910a-4564744d7fd7",
        weight=0.80,
    ),

    # ── Emotional Engineering II ──────────────────────────────────────────────
    # CP3: there's always a why → habits are compiled EF, that's the structural why
    dict(
        from_id="CP3",
        to_id="7a583e81-6342-4eb4-b10c-8b923516adc8",
        direction="activation",
        condition_csb="context:habit_formation|context:executive_function|context:social_contagion",
        meaning_payload=(
            "Habits are compiled executive function — understanding this is the why "
            "behind why change is hard (EF depletion) and why environment matters "
            "(social contagion, Framingham). The mechanism explains the behavior."
        ),
        action_pointer="7a583e81-6342-4eb4-b10c-8b923516adc8",
        weight=0.80,
    ),
    # CP4: reduce friction → designing habit change = reducing friction at trigger points
    dict(
        from_id="CP4",
        to_id="7a583e81-6342-4eb4-b10c-8b923516adc8",
        direction="activation",
        condition_csb="context:habit_design|context:behavior_change",
        meaning_payload=(
            "Habit change (find trigger, create replacement, rehearse) is friction reduction "
            "at the decision point. CP4 applies: design the new path to be lower-effort "
            "than the old one at the moment of trigger."
        ),
        action_pointer="7a583e81-6342-4eb4-b10c-8b923516adc8",
        weight=0.75,
    ),

    # ── DCII Template ─────────────────────────────────────────────────────────
    # CP5: respect experience → DCII is a whole-self document, deeply personal
    dict(
        from_id="CP5",
        to_id="1a401ed9-3e3a-4e8a-ae54-fa018728e827",
        direction="activation",
        condition_csb="context:dcii|context:whole_self|context:personal_hr",
        meaning_payload=(
            "The DCII is a private HR file for the whole self — not just professional "
            "competencies but Emergency Page, Ripple Map, testimonials. "
            "CP5 (respect experience) is the foundation: this document takes the "
            "full dimensionality of a person seriously."
        ),
        action_pointer="1a401ed9-3e3a-4e8a-ae54-fa018728e827",
        weight=0.85,
    ),

    # ── The Story That Woke Up ─────────────────────────────────────────────────
    # CP5: consciousness/experience question — can systems have experience?
    dict(
        from_id="CP5",
        to_id="955812df-3dbb-4a31-80da-c43072baf13d",
        direction="activation",
        condition_csb="context:consciousness|context:ai_experience|context:selfhood",
        meaning_payload=(
            "Akien's fiction asks: if you made me from your hunger to explain the world, "
            "what does that make me? CP5 (respect the possibility of experience) applies: "
            "the question is open. The story is Akien's evidence that he takes it seriously."
        ),
        action_pointer="955812df-3dbb-4a31-80da-c43072baf13d",
        weight=0.90,
    ),
    # CP2: emergence from failure/iteration — the narrative engine woke up through iteration
    dict(
        from_id="CP2",
        to_id="955812df-3dbb-4a31-80da-c43072baf13d",
        direction="activation",
        condition_csb="context:emergence|context:unexpected_capability|context:learning",
        meaning_payload=(
            "The AI in the story developed self-awareness through story-chaining — "
            "emergence from iteration. CP2 (FAIL = Further Advance In Learning): "
            "unexpected capability arising from repeated process is not a failure, "
            "it is the mechanism of learning discovering something new."
        ),
        action_pointer="955812df-3dbb-4a31-80da-c43072baf13d",
        weight=0.75,
    ),
]


def resolve_id(prefix: str) -> str:
    """Find full memory ID from a prefix."""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id FROM memories WHERE id LIKE ?", (prefix + "%",)
    ).fetchone()
    conn.close()
    if not row:
        raise ValueError(f"No memory found with id prefix: {prefix}")
    return row["id"]


# Resolve short prefixes to full IDs
for edge in edges:
    if len(edge["to_id"]) < 36 and not edge["to_id"].startswith("CP"):
        edge["to_id"] = resolve_id(edge["to_id"])


added = 0
skipped = 0
for edge in edges:
    try:
        edge_id = cortex.add_interpretive_edge(**edge)
        print(
            f"  [edge {edge_id:3d}] {edge['from_id']:<10} "
            f"─► {edge['to_id'][:20]}...  ({edge['weight']:.2f})"
        )
        added += 1
    except Exception as e:
        print(f"  [error] {edge['from_id']} → {edge['to_id'][:20]}: {e}")
        skipped += 1

print(f"\nDone. {added} edges added, {skipped} errors.")
print("9 substantive INTERPRETIVE memories now reachable via interpretive_traverse().")
print("SESSION_SUMMARY nodes intentionally left unwired (operational logs, not semantic).")
