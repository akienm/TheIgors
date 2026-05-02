"""
seed_conv_graph.py — D097: Format-conversion habit graph.

Seeded nodes:
  CONV:ROOT         — interpretive entry point hub
  CONV:EN_TO_CSB    — English prose → pipe-delimited CSB inline format
  CONV:CSB_TO_EN    — CSB inline → readable English
  CONV:EN_TO_DSB    — English prose → full DSB document
  CONV:DSB_TO_EN    — DSB document → readable English explanation
  CONV:CSB_TO_DSB   — CSB inline → full DSB document
  CONV:DSB_TO_CSB   — DSB document → CSB inline (compact)

Each PROCEDURAL node carries a prompt template in its narrative.
converter.py finds the right node via lists.conv, fills in {text}, calls LLM.

Run from repo root:
    python3 ~/TheIgors/lab/claudecode/seed_conv_graph.py
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

# ── CONV:ROOT hub ─────────────────────────────────────────────────────────────

conv_root = Memory(
    id="CONV:ROOT",
    narrative=(
        "Entry point for the format-conversion graph. "
        "All CONV:* conversion nodes are reachable from here. "
        "Supported formats: EN (English prose), CSB (pipe-delimited inline key:value), "
        "DSB (Distilled Structured Block document with DOC header and SECTION_* layout). "
        "Use lists.conv to look up a conversion node directly by key 'FROM_TO', e.g. 'EN_CSB'."
    ),
    memory_type=MemoryType.FACTUAL,
    metadata={
        "graph_role": "hub",
        "formats": ["EN", "CSB", "DSB"],
        "portable": True,
    },
)

# ── Conversion PROCEDURAL nodes ───────────────────────────────────────────────
# Narrative = prompt template. {text} is the only substitution variable.
# converter.py extracts everything between PROMPT_START and PROMPT_END.

conversions = [
    Memory(
        id="CONV:EN_TO_CSB",
        narrative=(
            "Convert English prose to CSB (Compressed Structured Block) inline format.\n"
            "CSB rules: pipe-delimited key|value pairs, one per line. "
            "No markdown. No blank lines. Abbreviate freely. "
            "First line: TYPE|<inferred_type>. Then key facts as KEY|value. "
            "Multi-value: KEY|v1,v2,v3. Sub-keys: KEY|field=value|field2=value2.\n"
            "PROMPT_START\n"
            "Convert the following English text to CSB format (pipe-delimited key|value, "
            "one entry per line, no markdown, abbreviate freely):\n\n{text}\n"
            "PROMPT_END"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "from_format": "EN",
            "to_format": "CSB",
            "trigger": "convert english to csb|en to csb|compress to csb",
            "portable": True,
        },
    ),
    Memory(
        id="CONV:CSB_TO_EN",
        narrative=(
            "Convert CSB (pipe-delimited inline key:value) to readable English prose.\n"
            "Expand abbreviations, form sentences, group related keys into paragraphs. "
            "Output should read naturally, no pipes or technical formatting visible.\n"
            "PROMPT_START\n"
            "Convert the following CSB (pipe-delimited key|value) format to clear English prose. "
            "Expand all abbreviations, group related items into paragraphs:\n\n{text}\n"
            "PROMPT_END"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "from_format": "CSB",
            "to_format": "EN",
            "trigger": "convert csb to english|csb to en|expand csb",
            "portable": True,
        },
    ),
    Memory(
        id="CONV:EN_TO_DSB",
        narrative=(
            "Convert English prose to DSB (Distilled Structured Block) document format.\n"
            "DSB rules: first line DOC|name|v1|updated=TODAY. "
            "Then META|, PURPOSE|, DESIGN_POINTS|, DECISIONS|, GAPS| sections as appropriate. "
            "Indent section content 2 spaces. No markdown, no blank lines within sections. "
            "Each section entry: KEY|value or  DP1|one-line-point style.\n"
            "PROMPT_START\n"
            "Convert the following English text to DSB (Distilled Structured Block) format. "
            "Start with DOC|<inferred_name>|v1|updated=TODAY. "
            "Use sections: META, PURPOSE, DESIGN_POINTS, DECISIONS, GAPS as appropriate. "
            "Indent section content 2 spaces. No markdown:\n\n{text}\n"
            "PROMPT_END"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "from_format": "EN",
            "to_format": "DSB",
            "trigger": "convert english to dsb|en to dsb|structure as dsb",
            "portable": True,
        },
    ),
    Memory(
        id="CONV:DSB_TO_EN",
        narrative=(
            "Convert a DSB document to readable English explanation.\n"
            "Expand the document into flowing prose: explain each section, "
            "expand abbreviations, connect the points into a coherent narrative. "
            "Suitable for human review or sending to someone unfamiliar with DSB.\n"
            "PROMPT_START\n"
            "Convert the following DSB (Distilled Structured Block) document to clear English. "
            "Explain each section, expand abbreviations, write it as flowing readable prose:\n\n{text}\n"
            "PROMPT_END"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "from_format": "DSB",
            "to_format": "EN",
            "trigger": "convert dsb to english|dsb to en|explain dsb",
            "portable": True,
        },
    ),
    Memory(
        id="CONV:CSB_TO_DSB",
        narrative=(
            "Convert CSB inline key:value pairs to a full DSB document.\n"
            "Infer a document name and appropriate section groupings from the keys. "
            "Output a valid DSB with DOC header and organized sections.\n"
            "PROMPT_START\n"
            "Convert the following CSB (pipe-delimited key|value) entries to a full DSB document. "
            "Infer a document name, group related keys into sections (META, PURPOSE, DESIGN_POINTS, etc.), "
            "and produce a valid DSB starting with DOC|<name>|v1|updated=TODAY:\n\n{text}\n"
            "PROMPT_END"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "from_format": "CSB",
            "to_format": "DSB",
            "trigger": "convert csb to dsb|csb to dsb|expand csb to document",
            "portable": True,
        },
    ),
    Memory(
        id="CONV:DSB_TO_CSB",
        narrative=(
            "Convert a DSB document to compact CSB inline format.\n"
            "Flatten all sections to key|value lines. Drop section headers. "
            "Abbreviate aggressively. Result should be pasteable inline without DSB scaffolding.\n"
            "PROMPT_START\n"
            "Convert the following DSB document to compact CSB (pipe-delimited key|value) inline format. "
            "Flatten sections to key|value lines, drop section headers, abbreviate aggressively:\n\n{text}\n"
            "PROMPT_END"
        ),
        memory_type=MemoryType.PROCEDURAL,
        metadata={
            "from_format": "DSB",
            "to_format": "CSB",
            "trigger": "convert dsb to csb|dsb to csb|compress dsb",
            "portable": True,
        },
    ),
]

# ── Store everything ──────────────────────────────────────────────────────────

cortex.store(conv_root)
print(f"stored: {conv_root.id}")

for c in conversions:
    cortex.store(c)
    print(f"stored: {c.id}")

# ── lists.conv fast-path ──────────────────────────────────────────────────────
# Key = "FROM_TO" (e.g. "EN_CSB"), value = memory ID
# list_get('lists.conv', 'EN_CSB') → 'CONV:EN_TO_CSB'

for c in conversions:
    from_fmt = c.metadata["from_format"]
    to_fmt = c.metadata["to_format"]
    key = f"{from_fmt}_{to_fmt}"
    cortex.list_set("lists.conv", key, c.id)
    cortex.list_set("lists.conv", c.id, c.id)  # also key by full ID
    print(f"  lists.conv[{key!r}] = {c.id}")

cortex.list_set("lists.conv", "ROOT", "CONV:ROOT")

# ── Interpretive edges ────────────────────────────────────────────────────────

edges = [
    ("CONV:ROOT", "CONV:EN_TO_CSB", "activation", "", "convert EN to CSB", ""),
    ("CONV:ROOT", "CONV:CSB_TO_EN", "activation", "", "convert CSB to EN", ""),
    ("CONV:ROOT", "CONV:EN_TO_DSB", "activation", "", "convert EN to DSB", ""),
    ("CONV:ROOT", "CONV:DSB_TO_EN", "activation", "", "convert DSB to EN", ""),
    ("CONV:ROOT", "CONV:CSB_TO_DSB", "activation", "", "convert CSB to DSB", ""),
    ("CONV:ROOT", "CONV:DSB_TO_CSB", "activation", "", "convert DSB to CSB", ""),
]

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
for key in ["EN_CSB", "CSB_EN", "EN_DSB", "DSB_EN", "CSB_DSB", "DSB_CSB"]:
    row = cortex.list_get("lists.conv", key)
    mem_id = row["item_value"] if row else None
    print(f"  list_get({key!r}) → {mem_id}")

traversal = cortex.interpretive_traverse(["CONV:ROOT"])
print(f"  traversal from ROOT: {[m.id for m in traversal]}")
