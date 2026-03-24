#!/usr/bin/env python3
"""
seed_cached_probe_instances.py — Seed CACHED_PROBE habit instances.

Engram CACHED_PROBE (pattern #21, Akien 2026-03-23) wraps resource monitors
in a payload-configured cache pattern.  Each instance produces two habits:
  - PROC_PROBE_<NAME>_CHECK   (threshold / heartbeat_tick — checks cache age)
  - PROC_PROBE_<NAME>_SURFACE (reactive / trigger_phrase — surfaces on demand)

Migration targets (T-cached-probe):
  1. disk-usage    → source: check_disk_usage  (was PROC_DISK_USAGE_CHECK)
  2. resource-load → source: check_resource_load (was PROC_RESOURCE_AWARENESS, archived)
  3. worker-queue  → source: check_worker_queue  (was PROC_WORKER_FOREMAN queue scan)

Usage:
    cd ~/TheIgors && source venv/bin/activate
    IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \\
        python claudecode/seed_cached_probe_instances.py

Verify:
    Igor: list_memories(type='PROCEDURAL') — look for PROC_PROBE_* entries
"""

import os
import sys
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
if DB_URL:
    os.environ["IGOR_HOME_DB_URL"] = DB_URL

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
cortex = Cortex(DB_PATH, instance_id="igor_wild_0001")

# ── CACHED_PROBE instance definitions ────────────────────────────────────────
# Each entry: (check_id, surface_id, probe_name, source_fn, trigger_phrase,
#              cache_ttl, worry_after, worry_fn, why)

PROBE_INSTANCES = [
    (
        "PROC_PROBE_DISK_USAGE_CHECK",
        "PROC_PROBE_DISK_USAGE_SURFACE",
        "disk-usage",
        "check_disk_usage",
        "check disk usage",
        300,  # cache_ttl: 5 min — disk usage changes slowly
        0,  # worry_after: 0 = disabled (threshold habits handle critical alerts)
        "",
        (
            "CACHED_PROBE migration of PROC_DISK_USAGE_CHECK. "
            "Disk state probed on heartbeat, cached 5min; surfaces on explicit request. "
            "Replaced bespoke action habit with payload-configured cache pattern (T-cached-probe)."
        ),
    ),
    (
        "PROC_PROBE_RESOURCE_LOAD_CHECK",
        "PROC_PROBE_RESOURCE_LOAD_SURFACE",
        "resource-load",
        "check_resource_load",
        "check resource load",
        60,  # cache_ttl: 1 min — CPU/RAM can change quickly
        0,  # worry_after: 0 = disabled (PROC_CPU_THRESHOLD / ResourceMonitorSource handle alerts)
        "",
        (
            "CACHED_PROBE migration of PROC_RESOURCE_AWARENESS (archived). "
            "Resource load probed on heartbeat, cached 60s; surfaces on explicit request. "
            "Threshold alerting remains in PROC_CPU_THRESHOLD + ResourceMonitorSource (T-cached-probe)."
        ),
    ),
    (
        "PROC_PROBE_WORKER_QUEUE_CHECK",
        "PROC_PROBE_WORKER_QUEUE_SURFACE",
        "worker-queue",
        "check_worker_queue",
        "check worker queue",
        30,  # cache_ttl: 30s — queue changes on each sprint completion
        300,  # worry_after: 5 min — if queue hasn't been checked in 5min, Igor should notice
        "check_worker_queue",
        (
            "CACHED_PROBE for CC task queue state. "
            "Queue summary probed on heartbeat, cached 30s; surfaces on explicit request. "
            "worry_after=300s: if queue is stale >5min, Igor is prompted to check it. "
            "Replaces inline queue scan in PROC_WORKER_FOREMAN (T-cached-probe)."
        ),
    ),
]


def _upsert(mem: Memory, parent_id: str = "CP1") -> str:
    existing = cortex.get(mem.id)
    if existing:
        existing.narrative = mem.narrative
        existing.metadata = mem.metadata
        cortex.store(existing)
        return "updated"
    else:
        cortex.store(mem)
        cortex.add_child(parent_id, mem.id)
        return "seeded"


def seed():
    print("Seeding CACHED_PROBE habit instances (T-cached-probe)\n")
    seeded = []
    updated = []
    errors = []

    for (
        check_id,
        surface_id,
        probe_name,
        source_fn,
        trigger_phrase,
        cache_ttl,
        worry_after,
        worry_fn,
        why,
    ) in PROBE_INSTANCES:

        # ── CHECK habit (threshold / heartbeat_tick) ─────────────────────────
        check_mem = Memory(
            id=check_id,
            narrative=(
                f"CACHED_PROBE check: {probe_name} — on heartbeat, check cache age; "
                f"if >{cache_ttl}s: refresh via {source_fn}. "
                + (
                    f"If >{worry_after}s stale: escalate via {worry_fn}. "
                    if worry_after
                    else ""
                )
            ),
            memory_type=MemoryType.PROCEDURAL,
            metadata={
                "habit_type": "threshold",
                "trigger": "heartbeat_tick",
                "code_ref": source_fn,
                "cache_ttl": cache_ttl,
                "worry_after": worry_after,
                "worry_fn": worry_fn,
                "probe_name": probe_name,
                "phase": "check",
                "pattern": "CACHED_PROBE",
                "template_id": "tpl-cached-probe",
                "tags": ["cached_probe", "monitor"],
                "inertia": 0.2,
                "why": why,
                "description": (
                    f"Periodic cache-age check for {probe_name}; "
                    f"refresh via {source_fn} when >{cache_ttl}s stale"
                ),
            },
            source="user_seeded",
            context_of_encoding=(
                f"T-cached-probe: CACHED_PROBE instance for {probe_name} — check habit"
            ),
            confidence=1.0,
        )

        # ── SURFACE habit (reactive / trigger_phrase) ────────────────────────
        surface_mem = Memory(
            id=surface_id,
            narrative=(
                f"CACHED_PROBE surface: {probe_name} — on '{trigger_phrase}', "
                f"surface cached value immediately via {source_fn}."
            ),
            memory_type=MemoryType.PROCEDURAL,
            metadata={
                "habit_type": "reactive",
                "trigger": trigger_phrase,
                "code_ref": source_fn,
                "cache_ttl": cache_ttl,
                "probe_name": probe_name,
                "phase": "surface",
                "pattern": "CACHED_PROBE",
                "template_id": "tpl-cached-probe",
                "tags": ["cached_probe"],
                "inertia": 0.2,
                "why": why,
                "description": (
                    f"On '{trigger_phrase}': surface cached {probe_name} value"
                ),
            },
            source="user_seeded",
            context_of_encoding=(
                f"T-cached-probe: CACHED_PROBE instance for {probe_name} — surface habit"
            ),
            confidence=1.0,
        )

        for mem in (check_mem, surface_mem):
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
    print("  list_memories(type='PROCEDURAL') — look for PROC_PROBE_* entries")
    print("  check disk usage  — triggers PROC_PROBE_DISK_USAGE_SURFACE")
    print("  check worker queue — triggers PROC_PROBE_WORKER_QUEUE_SURFACE")


if __name__ == "__main__":
    seed()
