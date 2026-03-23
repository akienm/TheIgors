#!/usr/bin/env python3
"""
Seed the WONDER Engram template as the first TEMPLATE Memory node.

WONDER is the simplest Engram pattern: given a topic trigger and a tool fn,
it instantiates one reactive habit that wonders (runs the tool, pushes result
to TWM, falls through to LLM for synthesis).

Usage:
    cd ~/TheIgors && source venv/bin/activate
    IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \
        python claudecode/seed_wonder_template.py

After seeding, verify with:
    Igor: list_templates()
    Igor: validate_template_schema(<wonder_schema_json>)
    Igor: instantiate_template("tpl-wonder", '{"trigger_phrase": "what am I working on", "tool_fn": "prim_twm_read"}')
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(
    os.environ.get(
        "IGOR_DB_PATH", os.path.expanduser("~/.TheIgors/igor_wild_0001/wild-0001.db")
    )
)


def get_cortex():
    return Cortex(DB_PATH)


WONDER_TEMPLATE_ID = "tpl-wonder"

WONDER_TEMPLATE_SCHEMA = {
    "pattern_name": "WONDER",
    "version": 1,
    "slot_manifest": [
        {
            "name": "trigger_phrase",
            "required": True,
            "type_hint": "str",
        },
        {
            "name": "tool_fn",
            "required": True,
            "type_hint": "str",
        },
        {
            "name": "twm_ttl",
            "required": False,
            "default": 60,
            "type_hint": "int",
        },
    ],
    "expansion_schema": [
        {
            "habit_type": "reactive",
            "name": "PROC_WONDER_{trigger_phrase|upper}",
            "trigger": "{trigger_phrase}",
            "narrative": "Wonder habit: {trigger_phrase}",
            "metadata": {
                "code_ref": "{tool_fn}",
                "twm_ttl_seconds": "{twm_ttl}",
                "description": "Wonder about {trigger_phrase} via {tool_fn}",
            },
        }
    ],
    "instantiation_contract": {
        "produces": ["reactive"],
        "condition_signature": "trigger='{trigger_phrase}'",
        "invariants": [
            "code_ref must be registered in tool registry",
        ],
        "edge_policy": "generate_fresh",
    },
}


def seed():
    cortex = get_cortex()
    mem = Memory(
        id=WONDER_TEMPLATE_ID,
        narrative=(
            "WONDER template — Engram pattern: given a topic trigger and a tool fn, "
            "instantiates one reactive habit that runs the tool and pushes the result "
            "to TWM for LLM synthesis."
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "template_schema": WONDER_TEMPLATE_SCHEMA,
        },
        source="user_seeded",
        context_of_encoding="T-template-schema: first TEMPLATE node; WONDER as worked example",
        confidence=1.0,
    )
    cortex.store(mem)
    print(f"Seeded TEMPLATE node: {WONDER_TEMPLATE_ID}")

    # Validate it round-trips cleanly
    stored = cortex.get(WONDER_TEMPLATE_ID)
    assert stored is not None, "FATAL: node not found after store"
    assert (
        stored.metadata.get("template_schema", {}).get("pattern_name") == "WONDER"
    ), "FATAL: template_schema not preserved"
    print("Validation: PASS — template_schema round-trips correctly")
    print()
    print("To test instantiation:")
    print(
        f'  instantiate_template("{WONDER_TEMPLATE_ID}", \'{{"trigger_phrase": "what am I processing", "tool_fn": "prim_twm_read"}}\')'
    )


if __name__ == "__main__":
    seed()
