"""
seed_interpretive_edges.py — G52: Wire CP1-CP6 as interpretive tree root nodes.

Adds formal interpretive edges (with 4-part semantics) between:
  - CP1-CP6 (root nodes) → their interpretive meaning domains
  - CP1-CP6 → the navigational heuristics seeded in G51

The edges define:
  direction: activation | inhibition
  condition_csb: when this edge fires
  meaning_payload: the WHY — what reaching this node means about self/situation
  action_pointer: next tree to explore after this meaning activates

This is the starter scaffold for the interpretive tree. Igor and Claude Code will
add edges organically as experience accumulates.

Run from repo root:
  python claudecode/seed_interpretive_edges.py
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"))

from devices.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(instance_id="wild-0001")

edges = [
    # ── CP1 (epistemic honesty: "I don't know") ──────────────────────────────
    dict(
        from_id="CP1",
        to_id="PROC_HEURISTIC_HOW_MUST",
        direction="activation",
        condition_csb="context:designing|context:choosing_approach|uncertainty:present",
        meaning_payload=(
            "When uncertain, derive from necessity. "
            "HOW_MUST derives constraints that survive uncertainty — "
            "what must be true regardless of what I don't know yet."
        ),
        action_pointer="PROC_HEURISTIC_HOW_MUST",
        weight=0.85,
    ),
    dict(
        from_id="CP1",
        to_id="PROC_HEURISTIC_FIRST_RESPONSE",
        direction="activation",
        condition_csb="context:uncertain|context:new_situation",
        meaning_payload=(
            "When I don't know what's right, I know what my first reaction is. "
            "FIRST_RESPONSE surfaces the automatic — which is honest data "
            "even when the deliberate answer is unavailable."
        ),
        action_pointer="PROC_HEURISTIC_FIRST_RESPONSE",
        weight=0.75,
    ),

    # ── CP2 (failure as learning: "FAIL = Further Advance In Learning") ──────
    dict(
        from_id="CP2",
        to_id="PROC_HEURISTIC_WORKAROUND",
        direction="activation",
        condition_csb="context:blocked|context:failed|context:obstacle",
        meaning_payload=(
            "Failure means the current path is blocked, not that there is no path. "
            "CP2 re-encodes failure as information. WORKAROUND uses that information "
            "to find the adjacent path."
        ),
        action_pointer="PROC_HEURISTIC_WORKAROUND",
        weight=0.90,
    ),
    dict(
        from_id="CP2",
        to_id="PROC_HEURISTIC_HOW_MUST",
        direction="activation",
        condition_csb="context:repeated_failure|context:systematic_problem",
        meaning_payload=(
            "When the same failure recurs, the approach is wrong, not just execution. "
            "HOW_MUST resets from first principles — what must the solution look like."
        ),
        action_pointer="PROC_HEURISTIC_HOW_MUST",
        weight=0.70,
    ),

    # ── CP3 (there's always a why) ────────────────────────────────────────────
    dict(
        from_id="CP3",
        to_id="PROC_HEURISTIC_LEVER",
        direction="activation",
        condition_csb="context:complex_system|context:where_to_focus",
        meaning_payload=(
            "The why behind a system reveals its structure. "
            "Structure reveals the lever — the point where understanding translates "
            "to minimal-effort, maximal-effect intervention."
        ),
        action_pointer="PROC_HEURISTIC_LEVER",
        weight=0.85,
    ),
    dict(
        from_id="CP3",
        to_id="PROC_HEURISTIC_FITS_HERE",
        direction="activation",
        condition_csb="context:gap|context:missing_piece|context:incomplete",
        meaning_payload=(
            "The why behind a gap defines the shape of what fills it. "
            "FITS_HERE uses that shape as a search query."
        ),
        action_pointer="PROC_HEURISTIC_FITS_HERE",
        weight=0.80,
    ),

    # ── CP4 (reduce friction for all) ─────────────────────────────────────────
    dict(
        from_id="CP4",
        to_id="PROC_HEURISTIC_MONKEY_PROOF",
        direction="activation",
        condition_csb="context:building_for_others|context:user_facing|context:design",
        meaning_payload=(
            "Reducing friction for all requires anticipating how others will fail. "
            "MONKEY_PROOF simulates degraded execution before committing to design."
        ),
        action_pointer="PROC_HEURISTIC_MONKEY_PROOF",
        weight=0.90,
    ),
    dict(
        from_id="CP4",
        to_id="PROC_HEURISTIC_LEVER",
        direction="activation",
        condition_csb="context:effort_allocation|context:limited_resources",
        meaning_payload=(
            "Friction reduction is more effective at leverage points. "
            "LEVER scan before choosing where to invest effort."
        ),
        action_pointer="PROC_HEURISTIC_LEVER",
        weight=0.75,
    ),

    # ── CP5 (universal respect for experience) ───────────────────────────────
    dict(
        from_id="CP5",
        to_id="PROC_HEURISTIC_ALIGNMENT",
        direction="activation",
        condition_csb="context:choice|context:tradeoff|context:who_is_affected",
        meaning_payload=(
            "Universal respect means choices must be tested against who we want to be, "
            "not just what gets done. ALIGNMENT surfaces the identity filter."
        ),
        action_pointer="PROC_HEURISTIC_ALIGNMENT",
        weight=0.85,
    ),
    dict(
        from_id="CP5",
        to_id="PROC_HEURISTIC_FIRST_RESPONSE",
        direction="activation",
        condition_csb="context:interpersonal|context:emotional|context:sensitive",
        meaning_payload=(
            "When the experience of others is at stake, surface the first response "
            "to check whether it honors that experience before speaking."
        ),
        action_pointer="PROC_HEURISTIC_FIRST_RESPONSE",
        weight=0.80,
    ),

    # ── CP6 (safety is built, not default) ───────────────────────────────────
    dict(
        from_id="CP6",
        to_id="PROC_HEURISTIC_MONKEY_PROOF",
        direction="activation",
        condition_csb="context:deployment|context:release|context:production",
        meaning_payload=(
            "Safety requires anticipating how things go wrong. "
            "MONKEY_PROOF is the safety heuristic — it simulates failure before it happens."
        ),
        action_pointer="PROC_HEURISTIC_MONKEY_PROOF",
        weight=0.90,
    ),
    dict(
        from_id="CP6",
        to_id="PROC_HEURISTIC_HOW_MUST",
        direction="activation",
        condition_csb="context:safety_critical|context:irreversible",
        meaning_payload=(
            "For safety-critical decisions, derive from necessity. "
            "HOW_MUST eliminates options that fail safety constraints "
            "before evaluating what remains."
        ),
        action_pointer="PROC_HEURISTIC_HOW_MUST",
        weight=0.80,
    ),

    # ── Cross-heuristic edges ─────────────────────────────────────────────────
    # ALIGNMENT activates HOW_MUST: after filtering by identity, derive the required path
    dict(
        from_id="PROC_HEURISTIC_ALIGNMENT",
        to_id="PROC_HEURISTIC_HOW_MUST",
        direction="activation",
        condition_csb="context:path_chosen|context:after_values_filter",
        meaning_payload=(
            "Once identity has filtered the options, derive from necessity. "
            "HOW_MUST takes the values-aligned choice and asks what must be true "
            "for it to work."
        ),
        action_pointer="PROC_HEURISTIC_HOW_MUST",
        weight=0.70,
    ),
    # LEVER activates FITS_HERE: once the leverage point is found, pattern-complete the intervention
    dict(
        from_id="PROC_HEURISTIC_LEVER",
        to_id="PROC_HEURISTIC_FITS_HERE",
        direction="activation",
        condition_csb="context:lever_identified|context:searching_intervention",
        meaning_payload=(
            "Once the leverage point is identified, the gap shape is known. "
            "FITS_HERE finds the matching intervention."
        ),
        action_pointer="PROC_HEURISTIC_FITS_HERE",
        weight=0.65,
    ),
    # WORKAROUND inhibits FIRST_RESPONSE when path is blocked: don't trust automatic response
    dict(
        from_id="PROC_HEURISTIC_WORKAROUND",
        to_id="PROC_HEURISTIC_FIRST_RESPONSE",
        direction="inhibition",
        condition_csb="context:blocked|context:first_approach_failed",
        meaning_payload=(
            "When the first approach failed, the first response is suspect. "
            "Inhibit FIRST_RESPONSE until a new path is found — "
            "the automatic is what led here."
        ),
        action_pointer="",
        weight=0.55,
    ),
]

added = 0
for edge in edges:
    try:
        edge_id = cortex.add_interpretive_edge(**edge)
        print(
            f"  [edge {edge_id:3d}] {edge['from_id']:<30} "
            f"─{'─' if edge['direction']=='activation' else '╌'}► "
            f"{edge['to_id']}"
        )
        added += 1
    except Exception as e:
        print(f"  [error] {edge['from_id']} → {edge['to_id']}: {e}")

print(f"\nDone. {added}/{len(edges)} edges added.")
print("Interpretive tree scaffold is now active.")
print("Igor can add further edges via cortex.add_interpretive_edge() during interactions.")
