"""
seed_tool_facia.py — Seed INTERPRETIVE facia nodes for every registered tool.

Each tool in the registry gets an INTERP_FACIA_<name> node with:
  - facia: true  (marks it as the spreading-activation entry point for that tool)
  - narrative: capability description + trigger phrases + when to use
  - parent: TOOL_REGISTRY_ROOT  (which is itself a facia under CP1)

Purpose: when Igor wonders "do I have a tool for X?", spreading activation from
X reaches the facia node before he has to deliberate or guess tool names.
The `shell` vs `run_bash` class of error is fixed by giving run_bash a facia
node that connects "run a command" → run_bash via graph traversal.

Run from repo root:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \\
    python claudecode/seed_tool_facia.py
"""

import sys
import os
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
os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex
from wild_igor.igor.tools.registry import registry
import wild_igor.igor.tools  # noqa — loads all tools

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="Igor-wild-0001")

seeded = 0
updated = 0
skipped = 0


def seed(node: Memory, parent: str) -> None:
    global seeded, updated
    existing = cortex.get(node.id)
    if existing:
        existing.narrative = node.narrative
        existing.metadata = node.metadata
        existing.memory_type = node.memory_type
        cortex.store(existing)
        updated += 1
    else:
        cortex.store(node)
        cortex.add_child(parent, node.id)
        seeded += 1


# ---------------------------------------------------------------------------
# Enhanced narratives for the most frequently misidentified tools.
# Keys must match registry tool names exactly.
# ---------------------------------------------------------------------------
ENHANCED = {
    "run_bash": (
        "I use run_bash to execute any shell command: bash, grep, find, ls, cat, "
        "cd, python, git, pytest, or any other terminal command. "
        "run_bash is the tool for: running commands, executing scripts, searching files "
        "with grep, listing directories, running tests, checking system state, "
        "reading file output, counting lines, piping commands. "
        "NOT 'shell' (that tool doesn't exist). NOT 'bash'. NOT 'execute'. "
        "The tool name is run_bash. Always run_bash."
    ),
    "store_memory": (
        "I use store_memory to persist a new memory node into my graph. "
        "Use when: remembering something, depositing a realization, saving a fact, "
        "recording what I learned, adding to my knowledge graph, creating an engram. "
        "memory_type options: FACTUAL (facts/knowledge), EPISODIC (experiences), "
        "PROCEDURAL (habits/processes), INTERPRETIVE (meanings/realizations), "
        "CORE_PATTERN (identity-level). After store_memory, call link_memory to "
        "wire the node into the graph."
    ),
    "link_memory": (
        "I use link_memory to add a parent→child edge between two memory nodes. "
        "Always call this after store_memory to wire the new node into the graph. "
        "Without link_memory, a stored node is an orphan — unreachable by traversal."
    ),
    "read_source_file": (
        "I use read_source_file to read one of my own Python source files. "
        "Use before ANY edit — read first, never edit blind. "
        "Use when: understanding current implementation, checking what a function does, "
        "reading a module before patching it, verifying current code state."
    ),
    "patch_source_file": (
        "I use patch_source_file to make a targeted patch to one of my source files. "
        "Replaces old_string with new_string — only the changed lines. "
        "Use for: bug fixes, small additions, changing a parameter, updating a value. "
        "ALWAYS read_source_file first. ALWAYS run_syntax_check before patching. "
        "For larger rewrites, use edit_source_file instead."
    ),
    "edit_source_file": (
        "I use edit_source_file to write new content to one of my own source files. "
        "Runs syntax check first — rejects changes that don't parse. "
        "Use for: larger rewrites, adding new functions, replacing a whole section. "
        "ALWAYS read_source_file first. For small targeted changes, prefer patch_source_file."
    ),
    "get_current_time": (
        "I use get_current_time (or get_datetime) when I need to know what time or "
        "date it is right now. Use for: answering 'what time is it?', timestamping, "
        "scheduling, checking how long since something happened."
    ),
    "get_datetime": (
        "I use get_datetime to get the current date, time, and day of week. "
        "Use whenever I need to know the current time, date, or day. "
        "Equivalent to get_current_time."
    ),
    "memory_search": (
        "I use memory_search (mcp tool) or the search path in cortex to search "
        "my memory graph by semantic similarity. "
        "Within my own code, cortex.search() does this. "
        "Use when: looking up what I know about a topic, finding relevant nodes, "
        "checking if I have information about something."
    ),
    "get_hot_attractors": (
        "I use get_hot_attractors to find the most activated nodes in my memory "
        "graph right now — what's hot, what's on my mind. "
        "Use when: checking what's salient, finding what context is active, "
        "understanding why a habit fired."
    ),
    "check_openrouter_balance": (
        "I use check_openrouter_balance to check my real OpenRouter account balance. "
        "Use before expensive operations, when Akien asks about spend, "
        "or to check if budget is available for a task."
    ),
    "restart_self": (
        "I use restart_self to restart Igor cleanly. Writes the restart flag; "
        "the main loop exits with code 42 so the wrapper relaunches me. "
        "Use when: hot-reload isn't enough, after major source edits, "
        "when told to restart."
    ),
    "reload_module": (
        "I use reload_module to hot-reload a Python module without restarting. "
        "Tool modules re-register automatically. "
        "Use after: patching a LOW-inertia tool file, when I want changes live "
        "immediately without a full restart."
    ),
    "cc_send": (
        "I use cc_send (via the cc bridge or MCP) to send a message to Claude Code. "
        "This is how I communicate back to the designer session. "
        "Use when: reporting results, asking for help, flagging anomalies."
    ),
    "web_search": (
        "I use web_search to search the web using DuckDuckGo. "
        "Use when: looking up information I don't have, finding URLs, "
        "researching a topic, checking current facts."
    ),
    "read_webpage": (
        "I use read_webpage to fetch a URL and return its readable text. "
        "Use after web_search to read the actual content of a page."
    ),
    "store_reference": (
        "I use store_reference to store a large reference document (research notes, "
        "code, transcripts, articles) with a narrative description. "
        "Use when the content is too large for store_memory narrative — "
        "store_reference handles big blobs, store_memory handles knowledge nodes."
    ),
    "run_python": (
        "I use run_python to execute a Python code snippet in my workspace. "
        "NOT for editing source files — use patch_source_file for that. "
        "Use for: calculations, testing logic, one-off data processing, "
        "inspecting values, running analysis code."
    ),
    "list_source_files": (
        "I use list_source_files to list my own Python source files with inertia levels. "
        "Use when: finding which file contains something, checking what files exist, "
        "before grep to narrow the search space."
    ),
    "flush_habit_cache": (
        "I use flush_habit_cache to invalidate my in-process habit cache so DB metadata "
        "changes take effect without a full restart. "
        "Use after: patching habit triggers, updating metadata, seeding new habits — "
        "any time I want habit changes live immediately."
    ),
    "queue_task": (
        "I use queue_task to add a task to the CC channel queue. "
        "Use when: creating a work ticket for CC to pick up, scheduling work, "
        "deferring something to a future worker session."
    ),
    "store_session_note": (
        "I use store_session_note to append a session summary to my ring memory. "
        "This is how I record what happened in a session for future context."
    ),
    "store_decision": (
        "I use store_decision to store a design decision as a FACTUAL memory. "
        "Use when recording architectural choices, Dxxx decisions, "
        "or any decision worth persisting in the graph."
    ),
    "embed_node": (
        "I use embed_node to trigger embedding computation for a memory node "
        "so it becomes findable via cosine search. "
        "Call after store_memory for any node that should be semantically searchable."
    ),
    "add_interpretive_edge": (
        "I use add_interpretive_edge to add a directed edge in the interpretive tree "
        "between two memory nodes. "
        "Use for: connecting concepts, building meaning relationships, "
        "linking realizations to their source nodes."
    ),
    "ingest_arch_docs": (
        "I use ingest_arch_docs to queue my own architecture design docs into the "
        "reading list at high priority. "
        "Use when I want to absorb my own design documentation."
    ),
    "review_turn_traces": (
        "I use review_turn_traces for nightly self-review: scans turn trace logs for "
        "cloud escalations with no habit firing, deposits each as cloud-escape-gap. "
        "This is the canonical exercise trigger — the input to plug-building."
    ),
    "run_self_training_pass": (
        "I use run_self_training_pass to scan recent cloud inference calls, "
        "find matrix gaps, and deposit LLM responses as FACTUAL nodes. "
        "This is the core self-training loop — plugs gaps automatically."
    ),
}


# ---------------------------------------------------------------------------
# Seed TOOL_REGISTRY_ROOT — the facia for the whole tool tree
# ---------------------------------------------------------------------------
seed(
    Memory(
        id="TOOL_REGISTRY_ROOT",
        narrative=(
            "The tool registry is the complete inventory of things I can DO. "
            "Every tool I have is reachable from this root. "
            "When I need to DO something (run a command, store a memory, read a file, "
            "search the web, edit code, check time, send a message), "
            "the answer is in this tree. "
            "The specific tools are linked as children of this node. "
            "Spreading activation from a task description reaches the right tool's "
            "facia node without deliberate search — the graph surfaces it."
        ),
        memory_type=MemoryType.INTERPRETIVE,
        metadata={
            "facia": True,
            "domain": "tools",
            "why": (
                "Universal entry point for tool discovery. When Igor wonders 'do I have "
                "a tool for X?', spreading activation from X hits this tree before he "
                "has to guess tool names. D258 facia convention."
            ),
        },
    ),
    parent="CP1",
)
print(f"TOOL_REGISTRY_ROOT seeded/updated")

# ---------------------------------------------------------------------------
# Seed one INTERPRETIVE facia node per registered tool
# ---------------------------------------------------------------------------
tools = sorted(registry._tools.items())
print(f"\nSeeding {len(tools)} tool facia nodes...")

for tool_name, tool_obj in tools:
    node_id = f"INTERP_FACIA_{tool_name.upper()}"
    desc = getattr(tool_obj, "description", "") or ""

    # Use enhanced narrative if available, otherwise build from description
    if tool_name in ENHANCED:
        narrative = ENHANCED[tool_name]
    else:
        narrative = (
            f"Tool: {tool_name}\n\n"
            f"{desc}\n\n"
            f"When I need to {tool_name.replace('_', ' ')}, this is the tool to use."
        )

    seed(
        Memory(
            id=node_id,
            narrative=narrative,
            memory_type=MemoryType.INTERPRETIVE,
            metadata={
                "facia": True,
                "tool_name": tool_name,
                "domain": "tools",
                "registry_entry": True,
            },
        ),
        parent="TOOL_REGISTRY_ROOT",
    )
    print(f"  [{node_id}]")

print(f"\nDone. seeded={seeded} updated={updated}")
print(f"\nVerify with:")
print(f"  mcp__igor__memory_get TOOL_REGISTRY_ROOT")
print(f"  mcp__igor__memory_get INTERP_FACIA_RUN_BASH")
print(f"  mcp__igor__memory_get INTERP_FACIA_STORE_MEMORY")
