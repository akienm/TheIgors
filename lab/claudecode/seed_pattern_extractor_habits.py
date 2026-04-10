#!/usr/bin/env python3
"""
seed_pattern_extractor_habits.py — Seed the 3 template-extractor habits.

T-template-extractor-habit: Igor can look at new Python code, recognize the
Engram pattern, extract slot values, and seed habits — without Claude Code.

Habits seeded:
  PROC_PATTERN_RECOGNIZE   — trigger: "recognize pattern" / "what pattern is this"
  PROC_TEMPLATE_PARAMETERIZE — trigger: "parameterize template" / "extract template params"
  PROC_TEMPLATE_INSTANTIATE  — trigger: "instantiate template" / "seed from template"
                               (thin wrapper; instantiate_template tool already exists)

These are delegation-type habits: BG scores and routes them to Igor's LLM
with the backing tool registered so LLM can call it directly.

Usage:
    cd ~/TheIgors && source venv/bin/activate
    IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \\
        python claudecode/seed_pattern_extractor_habits.py

Verify:
    Igor: list_memories(type='PROCEDURAL') | grep PROC_PATTERN
    Igor: recognize_pattern("def run_check(): if stale(cache): refresh()")
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
if DB_URL:
    os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="Igor-wild-0001")


# ── Habit definitions ─────────────────────────────────────────────────────────

HABITS = [
    Memory(
        id="PROC_PATTERN_RECOGNIZE",
        narrative=(
            "Recognize which Engram template pattern a given piece of Python code "
            "or habit description matches. Uses the 21-pattern inventory and LLM "
            "classification via recognize_pattern(). Returns pattern_name + confidence."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "delegation",
            "trigger": "recognize pattern",
            "trigger_phrases": [
                "recognize pattern",
                "what pattern is this",
                "which pattern",
                "identify pattern",
                "what template",
                "which template pattern",
            ],
            "code_ref": "recognize_pattern",
            "tags": ["template", "engram", "pattern_extractor"],
            "inertia": 0.2,
            "why": (
                "T-template-extractor-habit: closes the loop — Igor can classify "
                "new code/habits into the Engram vocabulary without Claude Code. "
                "First step in the recognize → parameterize → instantiate pipeline."
            ),
            "description": (
                "Given code or description, identify the best-matching Engram pattern."
            ),
        },
        source="user_seeded",
        context_of_encoding=(
            "T-template-extractor-habit: pattern recognition habit for Engram language"
        ),
        confidence=1.0,
    ),
    Memory(
        id="PROC_TEMPLATE_PARAMETERIZE",
        narrative=(
            "Extract slot values from Python code or a habit description, given an "
            "Engram pattern name. Uses parameterize_template() to produce the params "
            "JSON needed to call instantiate_template(). "
            "Use after PROC_PATTERN_RECOGNIZE to get the full pipeline."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "delegation",
            "trigger": "parameterize template",
            "trigger_phrases": [
                "parameterize template",
                "extract template params",
                "get template params",
                "extract parameters",
                "what are the params",
                "template parameters for",
            ],
            "code_ref": "parameterize_template",
            "tags": ["template", "engram", "pattern_extractor"],
            "inertia": 0.2,
            "why": (
                "T-template-extractor-habit: second step in the extraction pipeline. "
                "Bridges pattern recognition (PROC_PATTERN_RECOGNIZE) and seeding "
                "(PROC_TEMPLATE_INSTANTIATE) by extracting slot values from concrete code."
            ),
            "description": (
                "Given code + pattern name, extract slot values as JSON params."
            ),
        },
        source="user_seeded",
        context_of_encoding=(
            "T-template-extractor-habit: parameterization habit for Engram language"
        ),
        confidence=1.0,
    ),
    Memory(
        id="PROC_TEMPLATE_INSTANTIATE",
        narrative=(
            "Instantiate an Engram TEMPLATE node: given a template_id and JSON params, "
            "expand the template and seed the resulting habit nodes into the matrix. "
            "Wraps instantiate_template(). This is the final step in the pipeline: "
            "recognize → parameterize → instantiate."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "habit_type": "delegation",
            "trigger": "instantiate template",
            "trigger_phrases": [
                "instantiate template",
                "seed from template",
                "seed habits from",
                "expand template",
                "create habits from template",
                "seed template",
            ],
            "code_ref": "instantiate_template",
            "tags": ["template", "engram", "pattern_extractor"],
            "inertia": 0.2,
            "why": (
                "T-template-extractor-habit: final step — Igor seeds habits directly "
                "from the matrix without CC intervention. Completes the self-extending "
                "loop: recognize → parameterize → instantiate."
            ),
            "description": (
                "Given template_id + params JSON, expand and seed the habit nodes."
            ),
        },
        source="user_seeded",
        context_of_encoding=(
            "T-template-extractor-habit: instantiation habit for Engram language"
        ),
        confidence=1.0,
    ),
]


# ── Seeder ────────────────────────────────────────────────────────────────────


def _upsert(mem: Memory) -> str:
    existing = cortex.get(mem.id)
    if existing:
        cortex.store(mem)
        return "updated"
    cortex.store(mem)
    return "seeded"


def seed():
    print("Seeding pattern-extractor habits (T-template-extractor-habit)\n")
    seeded = []
    updated = []
    errors = []

    for mem in HABITS:
        try:
            action = _upsert(mem)
            if action == "seeded":
                seeded.append(mem.id)
            else:
                updated.append(mem.id)
            print(f"  [{action}] {mem.id}")
        except Exception as e:
            errors.append((mem.id, str(e)))
            print(f"  [ERROR] {mem.id}: {e}")

    print(
        f"\nDone — seeded: {len(seeded)}, updated: {len(updated)}, errors: {len(errors)}"
    )
    if errors:
        print("\nErrors:")
        for eid, emsg in errors:
            print(f"  ! {eid}: {emsg}")
        sys.exit(1)

    print("\nVerify with Igor:")
    print("  list_memories(type='PROCEDURAL') | grep PROC_PATTERN")
    print("  list_memories(type='PROCEDURAL') | grep PROC_TEMPLATE")
    print('  recognize_pattern("def run(): if stale: refresh()")')
    print("  what pattern is this: check_age → if stale → refresh → push TWM")


if __name__ == "__main__":
    seed()
