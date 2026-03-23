#!/usr/bin/env python3
"""
Seed all 21 Engram TEMPLATE nodes into the matrix.

Engram (Semon 1904) — the memory IS the program. Templates are macros that expand
into habits at seed time; at runtime there are only habits firing.

21 patterns (NINTH CRYSTALLIZATION, 2026-03-22):
  Original 10:  WONDER, FILE_ITERATOR, THRESHOLD_ALERT, SCHEDULER_TICK, READER_LOOP,
                MEMORY_DEPOSIT, SEARCH_AND_RESPOND, CONDITION_GATE, ERROR_RECOVERY,
                ASYNC_DELEGATE
  Igor's 10:    ESCALATION_LADDER, CURSOR_RESUME, BLOOM_INHIBIT, PREDICTION_CORRECTION,
                DISTILLATION, SIGNAL_DEBOUNCE, PRIMING, AFFECT_MODULATE, REFRAME,
                FANOUT_GATHER
  Akien's 1:    CACHED_PROBE

WONDER is the worked example from T-template-schema (tpl-wonder). This script skips
it if already present; seeds all others fresh.

Usage:
    cd ~/TheIgors && source venv/bin/activate
    IGOR_DB_PATH=~/.TheIgors/igor_wild_0001/wild-0001.db \\
        python claudecode/seed_templates.py

After seeding, verify with Igor tool:
    list_templates()
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(
    os.environ.get(
        "IGOR_DB_PATH",
        os.path.expanduser("~/.TheIgors/igor_wild_0001/wild-0001.db"),
    )
)


def get_cortex() -> Cortex:
    return Cortex(DB_PATH)


# ── Pattern definitions ────────────────────────────────────────────────────────
# Each entry: (template_id, narrative, template_schema)

TEMPLATES = [
    # ── Already seeded in T-template-schema — skip if present ──────────────────
    # tpl-wonder / WONDER is the worked example; included for completeness check
    # ── Original 10 patterns ──────────────────────────────────────────────────
    (
        "tpl-file-iterator",
        (
            "FILE_ITERATOR template — Engram pattern: open a batched source, "
            "read N items, process each, advance a persistent cursor, halt when "
            "exhausted. Re-triggerable; cursor survives restarts."
        ),
        {
            "pattern_name": "FILE_ITERATOR",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "iterator_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "source_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "processor_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "batch_size",
                    "required": False,
                    "default": 10,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 1000},
                },
                {
                    "name": "cursor_key",
                    "required": False,
                    "default": "cursor_pos",
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_file_iter_{{ iterator_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_FILE_ITER_{{ iterator_name | upper | replace('-', '_') }}",
                    "trigger": "file_iterator_tick_{{ iterator_name | snake }}",
                    "narrative": (
                        "FILE_ITERATOR: {{ iterator_name }} — read batch via {{ source_fn }}, "
                        "process via {{ processor_fn }}, advance cursor {{ cursor_key }}"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "file_iterator_tick_{{ iterator_name | snake }}",
                        "code_ref": "{{ processor_fn }}",
                        "source_fn": "{{ source_fn }}",
                        "batch_size": "{{ batch_size }}",
                        "cursor_key": "{{ cursor_key }}",
                        "pattern": "FILE_ITERATOR",
                        "tags": ["file_iterator"],
                        "description": (
                            "Read batch from {{ source_fn }}, process via {{ processor_fn }}, "
                            "advance cursor {{ cursor_key }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["action"],
                "condition_signature": "trigger='file_iterator_tick_{{ iterator_name | snake }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-threshold-alert",
        (
            "THRESHOLD_ALERT template — Engram pattern: monitor a scalar value, "
            "check it against a threshold, fire an alert action when exceeded, "
            "then enforce a cooldown window before re-firing."
        ),
        {
            "pattern_name": "THRESHOLD_ALERT",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "alert_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "monitor_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "threshold",
                    "required": True,
                    "type_hint": "float",
                    "validator": {"min": 0.0, "max": 1000000.0},
                },
                {
                    "name": "alert_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "cooldown_seconds",
                    "required": False,
                    "default": 300,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 86400},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_threshold_{{ alert_name | snake }}",
                    "habit_type": "threshold",
                    "name": "PROC_THRESHOLD_{{ alert_name | upper | replace('-', '_') }}",
                    "trigger": "heartbeat_tick",
                    "narrative": (
                        "THRESHOLD_ALERT: {{ alert_name }} — monitor {{ monitor_fn }}, "
                        "alert via {{ alert_fn }} when value exceeds {{ threshold }}"
                    ),
                    "metadata": {
                        "habit_type": "threshold",
                        "trigger": "heartbeat_tick",
                        "code_ref": "{{ monitor_fn }}",
                        "alert_fn": "{{ alert_fn }}",
                        "threshold": "{{ threshold }}",
                        "cooldown_seconds": "{{ cooldown_seconds }}",
                        "pattern": "THRESHOLD_ALERT",
                        "tags": ["threshold_alert", "monitor"],
                        "description": (
                            "Monitor via {{ monitor_fn }}; fire {{ alert_fn }} when > {{ threshold }}; "
                            "cooldown {{ cooldown_seconds }}s"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["threshold"],
                "condition_signature": "trigger='heartbeat_tick', threshold={{ threshold }}",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-scheduler-tick",
        (
            "SCHEDULER_TICK template — Engram pattern: fire periodically on an interval "
            "trigger, do work via a tick_fn, reschedule. Encodes cron-like recurring "
            "execution as a habit rather than a Python timer."
        ),
        {
            "pattern_name": "SCHEDULER_TICK",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "scheduler_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "tick_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "interval_seconds",
                    "required": False,
                    "default": 60,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 86400},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_sched_{{ scheduler_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_SCHED_{{ scheduler_name | upper | replace('-', '_') }}",
                    "trigger": "scheduler_tick_{{ scheduler_name | snake }}",
                    "narrative": (
                        "SCHEDULER_TICK: {{ scheduler_name }} — fire every {{ interval_seconds }}s, "
                        "execute {{ tick_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "scheduler_tick_{{ scheduler_name | snake }}",
                        "code_ref": "{{ tick_fn }}",
                        "interval_seconds": "{{ interval_seconds }}",
                        "pattern": "SCHEDULER_TICK",
                        "tags": ["scheduler"],
                        "description": (
                            "Periodic tick every {{ interval_seconds }}s via {{ tick_fn }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["action"],
                "condition_signature": "trigger='scheduler_tick_{{ scheduler_name | snake }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-reader-loop",
        (
            "READER_LOOP template — Engram pattern: pull an item from a queue or stream, "
            "parse it via a parser_fn, deposit the result as a Memory node, then "
            "acknowledge. The loop re-fires on the same trigger for the next item."
        ),
        {
            "pattern_name": "READER_LOOP",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "reader_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "queue_source",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "parser_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "deposit_type",
                    "required": False,
                    "default": "FACTUAL",
                    "type_hint": "str",
                    "validator": {
                        "enum": [
                            "FACTUAL",
                            "INTERPRETIVE",
                            "PROCEDURAL",
                            "EPISODIC",
                            "EXPERIENTIAL",
                        ]
                    },
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_reader_{{ reader_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_READER_{{ reader_name | upper | replace('-', '_') }}",
                    "trigger": "reader_loop_tick_{{ reader_name | snake }}",
                    "narrative": (
                        "READER_LOOP: {{ reader_name }} — pull from {{ queue_source }}, "
                        "parse via {{ parser_fn }}, deposit as {{ deposit_type }}"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "reader_loop_tick_{{ reader_name | snake }}",
                        "code_ref": "{{ parser_fn }}",
                        "queue_source": "{{ queue_source }}",
                        "deposit_type": "{{ deposit_type }}",
                        "pattern": "READER_LOOP",
                        "tags": ["reader_loop"],
                        "description": (
                            "Pull from {{ queue_source }}, parse via {{ parser_fn }}, "
                            "deposit {{ deposit_type }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["action"],
                "condition_signature": "trigger='reader_loop_tick_{{ reader_name | snake }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-memory-deposit",
        (
            "MEMORY_DEPOSIT template — Engram pattern: observe something that matches "
            "a trigger, classify it via a classifier_fn, and deposit it as a Memory node "
            "of the specified type. Passive_capture variant of the ingestion loop."
        ),
        {
            "pattern_name": "MEMORY_DEPOSIT",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "deposit_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\- ']+$"},
                },
                {
                    "name": "classifier_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "memory_type",
                    "required": False,
                    "default": "FACTUAL",
                    "type_hint": "str",
                    "validator": {
                        "enum": [
                            "FACTUAL",
                            "INTERPRETIVE",
                            "PROCEDURAL",
                            "EPISODIC",
                            "EXPERIENTIAL",
                        ]
                    },
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_deposit_{{ deposit_name | snake }}",
                    "habit_type": "passive_capture",
                    "name": "PROC_DEPOSIT_{{ deposit_name | upper | replace(' ', '_') | replace('-', '_') }}",
                    "trigger": "{{ deposit_name }}",
                    "narrative": (
                        "MEMORY_DEPOSIT: {{ deposit_name }} — classify via {{ classifier_fn }}, "
                        "store as {{ memory_type }}"
                    ),
                    "metadata": {
                        "habit_type": "passive_capture",
                        "trigger": "{{ deposit_name }}",
                        "code_ref": "{{ classifier_fn }}",
                        "deposit_type": "{{ memory_type }}",
                        "pattern": "MEMORY_DEPOSIT",
                        "tags": ["memory_deposit", "passive_capture"],
                        "description": (
                            "On '{{ deposit_name }}': classify via {{ classifier_fn }}, "
                            "deposit {{ memory_type }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["passive_capture"],
                "condition_signature": "trigger='{{ deposit_name }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-search-and-respond",
        (
            "SEARCH_AND_RESPOND template — Engram pattern: query → cortex.search → "
            "format results → push to TWM for LLM synthesis. The canonical retrieval "
            "pattern; WONDER is the specialized single-tool variant."
        ),
        {
            "pattern_name": "SEARCH_AND_RESPOND",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9 _\-']+$"},
                },
                {
                    "name": "search_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "depth",
                    "required": False,
                    "default": "medium",
                    "type_hint": "str",
                    "validator": {"enum": ["shallow", "medium", "deep"]},
                },
                {
                    "name": "twm_ttl",
                    "required": False,
                    "default": 120,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 3600},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_sar_{{ trigger_phrase | snake }}",
                    "habit_type": "reactive",
                    "name": "PROC_SAR_{{ trigger_phrase | upper | replace(' ', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "SEARCH_AND_RESPOND: {{ trigger_phrase }} — search via {{ search_fn }} "
                        "at {{ depth }} depth, push result to TWM"
                    ),
                    "metadata": {
                        "habit_type": "reactive",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ search_fn }}",
                        "search_depth": "{{ depth }}",
                        "twm_ttl_seconds": "{{ twm_ttl }}",
                        "pattern": "SEARCH_AND_RESPOND",
                        "tags": ["search_and_respond"],
                        "description": (
                            "On '{{ trigger_phrase }}': search via {{ search_fn }} "
                            "({{ depth }}), push to TWM for {{ twm_ttl }}s"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["reactive"],
                "condition_signature": "trigger='{{ trigger_phrase }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-condition-gate",
        (
            "CONDITION_GATE template — Engram pattern: check a boolean condition via "
            "condition_fn; if True, fire action_fn; if False, suppress. Encodes "
            "if-then-else as a habit without code changes. May be the primitive that "
            "BLOOM_INHIBIT and THRESHOLD_ALERT derive from."
        ),
        {
            "pattern_name": "CONDITION_GATE",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "gate_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "condition_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "action_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "suppress_fn",
                    "required": False,
                    "default": "",
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_gate_{{ gate_name | snake }}",
                    "habit_type": "cognitive",
                    "name": "PROC_GATE_{{ gate_name | upper | replace('-', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "CONDITION_GATE: {{ gate_name }} — check {{ condition_fn }}, "
                        "if true: {{ action_fn }}, if false: suppress"
                    ),
                    "metadata": {
                        "habit_type": "cognitive",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ condition_fn }}",
                        "action_fn": "{{ action_fn }}",
                        "suppress_fn": "{{ suppress_fn }}",
                        "pattern": "CONDITION_GATE",
                        "tags": ["condition_gate"],
                        "description": (
                            "Gate on {{ condition_fn }}; pass → {{ action_fn }}; "
                            "block → {{ suppress_fn or 'suppress' }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["cognitive"],
                "condition_signature": "trigger='{{ trigger_phrase }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-error-recovery",
        (
            "ERROR_RECOVERY template — Engram pattern: attempt an action, catch errors, "
            "classify them via error_classifier_fn, retry up to retry_limit times, "
            "then escalate via escalate_fn if all retries exhausted."
        ),
        {
            "pattern_name": "ERROR_RECOVERY",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "recovery_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "action_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "error_classifier_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "escalate_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "retry_limit",
                    "required": False,
                    "default": 3,
                    "type_hint": "int",
                    "validator": {"min": 0, "max": 10},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_errec_{{ recovery_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_ERREC_{{ recovery_name | upper | replace('-', '_') }}",
                    "trigger": "error_recovery_trigger_{{ recovery_name | snake }}",
                    "narrative": (
                        "ERROR_RECOVERY: {{ recovery_name }} — try {{ action_fn }}, "
                        "retry {{ retry_limit }}x, escalate via {{ escalate_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "error_recovery_trigger_{{ recovery_name | snake }}",
                        "code_ref": "{{ action_fn }}",
                        "error_classifier_fn": "{{ error_classifier_fn }}",
                        "escalate_fn": "{{ escalate_fn }}",
                        "retry_limit": "{{ retry_limit }}",
                        "pattern": "ERROR_RECOVERY",
                        "tags": ["error_recovery"],
                        "description": (
                            "Try {{ action_fn }}, classify error via {{ error_classifier_fn }}, "
                            "retry {{ retry_limit }}x, then {{ escalate_fn }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["action"],
                "condition_signature": (
                    "trigger='error_recovery_trigger_{{ recovery_name | snake }}'"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-async-delegate",
        (
            "ASYNC_DELEGATE template — Engram pattern: trigger → spawn one asynchronous "
            "delegation → optionally await result in a separate habit. Fire and continue "
            "vs fire and forget controlled by await_result slot."
        ),
        {
            "pattern_name": "ASYNC_DELEGATE",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "delegate_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "delegate_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "result_key",
                    "required": False,
                    "default": "",
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_delegate_{{ delegate_name | snake }}",
                    "habit_type": "delegation",
                    "name": "PROC_DELEGATE_{{ delegate_name | upper | replace('-', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "ASYNC_DELEGATE: {{ delegate_name }} — on '{{ trigger_phrase }}', "
                        "spawn {{ delegate_fn }}, result_key={{ result_key or 'none' }}"
                    ),
                    "metadata": {
                        "habit_type": "delegation",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ delegate_fn }}",
                        "result_key": "{{ result_key }}",
                        "pattern": "ASYNC_DELEGATE",
                        "tags": ["async_delegate", "delegation"],
                        "description": (
                            "On '{{ trigger_phrase }}': delegate to {{ delegate_fn }}, "
                            "store result in TWM key '{{ result_key }}'"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["delegation"],
                "condition_signature": "trigger='{{ trigger_phrase }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    # ── Igor's 10 patterns ─────────────────────────────────────────────────────
    (
        "tpl-escalation-ladder",
        (
            "ESCALATION_LADDER template — Engram pattern: try tier.1 → fail → try "
            "tier.2 → fail → … → tier.N. Progressive resource escalation. Distinct "
            "from ERROR_RECOVERY (which retries the same level); this climbs through "
            "qualitatively different resource levels."
        ),
        {
            "pattern_name": "ESCALATION_LADDER",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "ladder_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "tier1_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "tier2_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "tier3_fn",
                    "required": False,
                    "default": "",
                    "type_hint": "str",
                },
                {
                    "name": "final_fallback_fn",
                    "required": True,
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_ladder_{{ ladder_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_LADDER_{{ ladder_name | upper | replace('-', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "ESCALATION_LADDER: {{ ladder_name }} — try {{ tier1_fn }} → "
                        "{{ tier2_fn }} → {{ tier3_fn or tier2_fn }} → fallback {{ final_fallback_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ tier1_fn }}",
                        "tier2_fn": "{{ tier2_fn }}",
                        "tier3_fn": "{{ tier3_fn }}",
                        "final_fallback_fn": "{{ final_fallback_fn }}",
                        "pattern": "ESCALATION_LADDER",
                        "tags": ["escalation_ladder"],
                        "description": (
                            "Progressive escalation: {{ tier1_fn }} → {{ tier2_fn }} → "
                            "{{ tier3_fn or '(skip)' }} → {{ final_fallback_fn }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["action"],
                "condition_signature": "trigger='{{ trigger_phrase }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-cursor-resume",
        (
            "CURSOR_RESUME template — Engram pattern: load checkpoint from persistent "
            "store, process a batch, save cursor, halt. Restarts from cursor on next "
            "invocation. Distinct from FILE_ITERATOR: cursor survives process restarts "
            "and is explicitly managed per-session."
        ),
        {
            "pattern_name": "CURSOR_RESUME",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "job_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "batch_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "cursor_store_key",
                    "required": False,
                    "default": "cursor",
                    "type_hint": "str",
                },
                {
                    "name": "batch_size",
                    "required": False,
                    "default": 50,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 10000},
                },
                {
                    "name": "complete_fn",
                    "required": False,
                    "default": "",
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_cursor_{{ job_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_CURSOR_{{ job_name | upper | replace('-', '_') }}",
                    "trigger": "cursor_resume_tick_{{ job_name | snake }}",
                    "narrative": (
                        "CURSOR_RESUME: {{ job_name }} — load cursor {{ cursor_store_key }}, "
                        "batch {{ batch_size }} via {{ batch_fn }}, save, halt"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "cursor_resume_tick_{{ job_name | snake }}",
                        "code_ref": "{{ batch_fn }}",
                        "cursor_store_key": "{{ cursor_store_key }}",
                        "batch_size": "{{ batch_size }}",
                        "complete_fn": "{{ complete_fn }}",
                        "pattern": "CURSOR_RESUME",
                        "tags": ["cursor_resume"],
                        "description": (
                            "Resumable batch job: {{ batch_fn }}, batch={{ batch_size }}, "
                            "cursor_key={{ cursor_store_key }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["action"],
                "condition_signature": "trigger='cursor_resume_tick_{{ job_name | snake }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-bloom-inhibit",
        (
            "BLOOM_INHIBIT template — Engram pattern: score all candidates simultaneously, "
            "apply lateral inhibition (losers suppressed in proportion to winner's score), "
            "winner emerges. This IS the BG scoring model expressed as a pattern. "
            "May be the primitive from which CONDITION_GATE and THRESHOLD_ALERT derive."
        ),
        {
            "pattern_name": "BLOOM_INHIBIT",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "selection_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "candidates_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "score_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "winner_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "inhibit_threshold",
                    "required": False,
                    "default": 0.5,
                    "type_hint": "float",
                    "validator": {"min": 0.0, "max": 1.0},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_bloom_{{ selection_name | snake }}",
                    "habit_type": "cognitive",
                    "name": "PROC_BLOOM_{{ selection_name | upper | replace('-', '_') }}",
                    "trigger": "bloom_inhibit_tick_{{ selection_name | snake }}",
                    "narrative": (
                        "BLOOM_INHIBIT: {{ selection_name }} — score all via {{ score_fn }}, "
                        "inhibit below {{ inhibit_threshold }}, pass winner to {{ winner_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "cognitive",
                        "trigger": "bloom_inhibit_tick_{{ selection_name | snake }}",
                        "code_ref": "{{ candidates_fn }}",
                        "score_fn": "{{ score_fn }}",
                        "winner_fn": "{{ winner_fn }}",
                        "inhibit_threshold": "{{ inhibit_threshold }}",
                        "pattern": "BLOOM_INHIBIT",
                        "tags": ["bloom_inhibit", "lateral_inhibition"],
                        "description": (
                            "Parallel scoring via {{ score_fn }}, lateral inhibition "
                            "at {{ inhibit_threshold }}, winner → {{ winner_fn }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["cognitive"],
                "condition_signature": (
                    "trigger='bloom_inhibit_tick_{{ selection_name | snake }}'"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-prediction-correction",
        (
            "PREDICTION_CORRECTION template — Engram pattern: predict an outcome, "
            "observe the actual, compute the delta, update weights. This IS the NE "
            "prospective/actual pair expressed as a pattern. The learning loop in "
            "execution — each turn is prediction + correction."
        ),
        {
            "pattern_name": "PREDICTION_CORRECTION",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "predictor_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "predict_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "observe_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "update_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "learning_rate",
                    "required": False,
                    "default": 0.1,
                    "type_hint": "float",
                    "validator": {"min": 0.001, "max": 1.0},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_predcorr_{{ predictor_name | snake }}_predict",
                    "habit_type": "cognitive",
                    "name": "PROC_PRED_{{ predictor_name | upper | replace('-', '_') }}_PREDICT",
                    "trigger": "prediction_cycle_start_{{ predictor_name | snake }}",
                    "narrative": (
                        "PREDICTION_CORRECTION predict half: {{ predictor_name }} — "
                        "run {{ predict_fn }}, deposit prediction"
                    ),
                    "metadata": {
                        "habit_type": "cognitive",
                        "trigger": "prediction_cycle_start_{{ predictor_name | snake }}",
                        "code_ref": "{{ predict_fn }}",
                        "observe_fn": "{{ observe_fn }}",
                        "update_fn": "{{ update_fn }}",
                        "learning_rate": "{{ learning_rate }}",
                        "phase": "predict",
                        "pattern": "PREDICTION_CORRECTION",
                        "tags": ["prediction_correction"],
                        "description": (
                            "Predict via {{ predict_fn }}, await observation"
                        ),
                    },
                },
                {
                    "id": "proc_predcorr_{{ predictor_name | snake }}_update",
                    "habit_type": "cognitive",
                    "name": "PROC_PRED_{{ predictor_name | upper | replace('-', '_') }}_UPDATE",
                    "trigger": "prediction_cycle_result_{{ predictor_name | snake }}",
                    "narrative": (
                        "PREDICTION_CORRECTION update half: {{ predictor_name }} — "
                        "observe via {{ observe_fn }}, delta → {{ update_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "cognitive",
                        "trigger": "prediction_cycle_result_{{ predictor_name | snake }}",
                        "code_ref": "{{ observe_fn }}",
                        "update_fn": "{{ update_fn }}",
                        "learning_rate": "{{ learning_rate }}",
                        "phase": "update",
                        "pattern": "PREDICTION_CORRECTION",
                        "tags": ["prediction_correction"],
                        "description": (
                            "Observe actual, delta → update weights via {{ update_fn }} "
                            "at lr={{ learning_rate }}"
                        ),
                    },
                },
            ],
            "instantiation_contract": {
                "produces": ["cognitive", "cognitive"],
                "condition_signature": (
                    "trigger='prediction_cycle_start_{{ predictor_name | snake }}' "
                    "| 'prediction_cycle_result_{{ predictor_name | snake }}'"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-distillation",
        (
            "DISTILLATION template — Engram pattern: cluster related EPISODIC nodes, "
            "extract the common pattern via pattern_fn, deposit a higher-type node "
            "(INTERPRETIVE or PROCEDURAL). The only Engram primitive that compresses "
            "rather than grows. MOST IMPORTANT MISSING PATTERN — matrix compression "
            "toward understanding."
        ),
        {
            "pattern_name": "DISTILLATION",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "distillation_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "cluster_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "pattern_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "source_type",
                    "required": False,
                    "default": "EPISODIC",
                    "type_hint": "str",
                    "validator": {
                        "enum": [
                            "EPISODIC",
                            "EXPERIENTIAL",
                            "FACTUAL",
                        ]
                    },
                },
                {
                    "name": "target_type",
                    "required": False,
                    "default": "INTERPRETIVE",
                    "type_hint": "str",
                    "validator": {
                        "enum": [
                            "INTERPRETIVE",
                            "PROCEDURAL",
                            "CORE_PATTERN",
                        ]
                    },
                },
                {
                    "name": "min_cluster_size",
                    "required": False,
                    "default": 3,
                    "type_hint": "int",
                    "validator": {"min": 2, "max": 100},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_distill_{{ distillation_name | snake }}",
                    "habit_type": "cognitive",
                    "name": "PROC_DISTILL_{{ distillation_name | upper | replace('-', '_') }}",
                    "trigger": "distillation_tick_{{ distillation_name | snake }}",
                    "narrative": (
                        "DISTILLATION: {{ distillation_name }} — cluster {{ source_type }} nodes "
                        "via {{ cluster_fn }}, extract pattern via {{ pattern_fn }}, "
                        "deposit {{ target_type }}"
                    ),
                    "metadata": {
                        "habit_type": "cognitive",
                        "trigger": "distillation_tick_{{ distillation_name | snake }}",
                        "code_ref": "{{ cluster_fn }}",
                        "pattern_fn": "{{ pattern_fn }}",
                        "source_type": "{{ source_type }}",
                        "target_type": "{{ target_type }}",
                        "min_cluster_size": "{{ min_cluster_size }}",
                        "pattern": "DISTILLATION",
                        "tags": ["distillation", "compression"],
                        "description": (
                            "Cluster {{ min_cluster_size }}+ {{ source_type }} nodes → "
                            "extract via {{ pattern_fn }} → deposit {{ target_type }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["cognitive"],
                "condition_signature": (
                    "trigger='distillation_tick_{{ distillation_name | snake }}'"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-signal-debounce",
        (
            "SIGNAL_DEBOUNCE template — Engram pattern: receive a signal, wait N seconds, "
            "fire only if signal still persists, then enforce a cooldown. Prevents "
            "spurious triggers on transient spikes. Distinct from THRESHOLD_ALERT "
            "(accumulation-based); this is persistence-based."
        ),
        {
            "pattern_name": "SIGNAL_DEBOUNCE",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "signal_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "fire_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "wait_seconds",
                    "required": False,
                    "default": 5,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 3600},
                },
                {
                    "name": "cooldown_seconds",
                    "required": False,
                    "default": 30,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 86400},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_debounce_{{ signal_name | snake }}",
                    "habit_type": "reactive",
                    "name": "PROC_DEBOUNCE_{{ signal_name | upper | replace('-', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "SIGNAL_DEBOUNCE: {{ signal_name }} — wait {{ wait_seconds }}s, "
                        "fire {{ fire_fn }} if persists, cooldown {{ cooldown_seconds }}s"
                    ),
                    "metadata": {
                        "habit_type": "reactive",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ fire_fn }}",
                        "wait_seconds": "{{ wait_seconds }}",
                        "cooldown_seconds": "{{ cooldown_seconds }}",
                        "pattern": "SIGNAL_DEBOUNCE",
                        "tags": ["signal_debounce"],
                        "description": (
                            "Debounce '{{ trigger_phrase }}': wait {{ wait_seconds }}s, "
                            "fire {{ fire_fn }} if still active, cooldown {{ cooldown_seconds }}s"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["reactive"],
                "condition_signature": "trigger='{{ trigger_phrase }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-priming",
        (
            "PRIMING template — Engram pattern: activate a concept A, raise the base "
            "probability for related concepts B for a time window, then decay back. "
            "Anticipatory, not reactive — pre-activates paths before they're needed. "
            "Distinct from WONDER/SEARCH (which are reactive); PRIMING raises readiness."
        ),
        {
            "pattern_name": "PRIMING",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "prime_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "prime_trigger",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "prime_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "window_seconds",
                    "required": False,
                    "default": 300,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 3600},
                },
                {
                    "name": "boost_weight",
                    "required": False,
                    "default": 0.2,
                    "type_hint": "float",
                    "validator": {"min": 0.01, "max": 1.0},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_prime_{{ prime_name | snake }}",
                    "habit_type": "context_inject",
                    "name": "PROC_PRIME_{{ prime_name | upper | replace('-', '_') }}",
                    "trigger": "{{ prime_trigger }}",
                    "narrative": (
                        "PRIMING: {{ prime_name }} — on '{{ prime_trigger }}', boost related "
                        "concepts via {{ prime_fn }} by {{ boost_weight }} for {{ window_seconds }}s"
                    ),
                    "metadata": {
                        "habit_type": "context_inject",
                        "trigger": "{{ prime_trigger }}",
                        "code_ref": "{{ prime_fn }}",
                        "window_seconds": "{{ window_seconds }}",
                        "boost_weight": "{{ boost_weight }}",
                        "pattern": "PRIMING",
                        "tags": ["priming", "anticipatory"],
                        "description": (
                            "Prime on '{{ prime_trigger }}': boost {{ boost_weight }} "
                            "for {{ window_seconds }}s via {{ prime_fn }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["context_inject"],
                "condition_signature": "trigger='{{ prime_trigger }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-affect-modulate",
        (
            "AFFECT_MODULATE template — Engram pattern: read the milieu state "
            "(valence/arousal/dominance), adjust thresholds or weights across all "
            "active habits via adjust_fn when the milieu dimension crosses a threshold. "
            "Milieu as a pervasive parameter — global tuning, not per-habit."
        ),
        {
            "pattern_name": "AFFECT_MODULATE",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "modulator_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "milieu_dimension",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"enum": ["valence", "arousal", "dominance"]},
                },
                {
                    "name": "threshold",
                    "required": True,
                    "type_hint": "float",
                    "validator": {"min": -1.0, "max": 1.0},
                },
                {
                    "name": "adjust_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "scope",
                    "required": False,
                    "default": "global",
                    "type_hint": "str",
                    "validator": {"enum": ["global", "tagged", "named"]},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_affmod_{{ modulator_name | snake }}",
                    "habit_type": "threshold",
                    "name": "PROC_AFFMOD_{{ modulator_name | upper | replace('-', '_') }}",
                    "trigger": "heartbeat_tick",
                    "narrative": (
                        "AFFECT_MODULATE: {{ modulator_name }} — when milieu.{{ milieu_dimension }} "
                        "crosses {{ threshold }}, run {{ adjust_fn }} on {{ scope }} habits"
                    ),
                    "metadata": {
                        "habit_type": "threshold",
                        "trigger": "heartbeat_tick",
                        "code_ref": "{{ adjust_fn }}",
                        "milieu_dimension": "{{ milieu_dimension }}",
                        "threshold": "{{ threshold }}",
                        "scope": "{{ scope }}",
                        "pattern": "AFFECT_MODULATE",
                        "tags": ["affect_modulate", "milieu"],
                        "description": (
                            "When milieu.{{ milieu_dimension }} ≥ {{ threshold }}: "
                            "{{ adjust_fn }} on {{ scope }} scope"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["threshold"],
                "condition_signature": (
                    "trigger='heartbeat_tick', milieu_dimension={{ milieu_dimension }}, "
                    "threshold={{ threshold }}"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-reframe",
        (
            "REFRAME template — Engram pattern: observe input X, apply an interpretive "
            "lens via lens_fn, produce a new meaning payload, push the modified "
            "observation. Encodes interpretive traverse as a habit — reframe IS the "
            "interpretive_edges mechanism expressed as a pattern."
        ),
        {
            "pattern_name": "REFRAME",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "reframe_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "lens_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "push_fn",
                    "required": False,
                    "default": "prim_twm_push",
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_reframe_{{ reframe_name | snake }}",
                    "habit_type": "cognitive",
                    "name": "PROC_REFRAME_{{ reframe_name | upper | replace('-', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "REFRAME: {{ reframe_name }} — apply lens {{ lens_fn }} to "
                        "'{{ trigger_phrase }}', push reframed obs via {{ push_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "cognitive",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ lens_fn }}",
                        "push_fn": "{{ push_fn }}",
                        "pattern": "REFRAME",
                        "tags": ["reframe", "interpretive"],
                        "description": (
                            "On '{{ trigger_phrase }}': lens {{ lens_fn }}, push via {{ push_fn }}"
                        ),
                    },
                }
            ],
            "instantiation_contract": {
                "produces": ["cognitive"],
                "condition_signature": "trigger='{{ trigger_phrase }}'",
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    (
        "tpl-fanout-gather",
        (
            "FANOUT_GATHER template — Engram pattern: trigger → N parallel delegations "
            "→ wait for all to complete → merge results → continue. Distinct from "
            "ASYNC_DELEGATE (one branch, fire-and-continue); this fans out and "
            "gathers before proceeding."
        ),
        {
            "pattern_name": "FANOUT_GATHER",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "fanout_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "fanout_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "merge_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "timeout_seconds",
                    "required": False,
                    "default": 30,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 300},
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_fanout_{{ fanout_name | snake }}",
                    "habit_type": "delegation",
                    "name": "PROC_FANOUT_{{ fanout_name | upper | replace('-', '_') }}",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "FANOUT_GATHER fanout: {{ fanout_name }} — spawn N delegations "
                        "via {{ fanout_fn }}, timeout {{ timeout_seconds }}s"
                    ),
                    "metadata": {
                        "habit_type": "delegation",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ fanout_fn }}",
                        "timeout_seconds": "{{ timeout_seconds }}",
                        "gather_trigger": "fanout_gather_done_{{ fanout_name | snake }}",
                        "pattern": "FANOUT_GATHER",
                        "phase": "fanout",
                        "tags": ["fanout_gather"],
                        "description": (
                            "Fan out via {{ fanout_fn }}, signal gather when all done"
                        ),
                    },
                },
                {
                    "id": "proc_gather_{{ fanout_name | snake }}",
                    "habit_type": "action",
                    "name": "PROC_GATHER_{{ fanout_name | upper | replace('-', '_') }}",
                    "trigger": "fanout_gather_done_{{ fanout_name | snake }}",
                    "narrative": (
                        "FANOUT_GATHER gather: {{ fanout_name }} — merge results "
                        "via {{ merge_fn }}, push to TWM"
                    ),
                    "metadata": {
                        "habit_type": "action",
                        "trigger": "fanout_gather_done_{{ fanout_name | snake }}",
                        "code_ref": "{{ merge_fn }}",
                        "fanout_name": "{{ fanout_name }}",
                        "pattern": "FANOUT_GATHER",
                        "phase": "gather",
                        "tags": ["fanout_gather"],
                        "description": (
                            "Gather all branches, merge via {{ merge_fn }}, push result"
                        ),
                    },
                },
            ],
            "instantiation_contract": {
                "produces": ["delegation", "action"],
                "condition_signature": (
                    "trigger='{{ trigger_phrase }}' | "
                    "'fanout_gather_done_{{ fanout_name | snake }}'"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
    # ── Akien's addition ────────────────────────────────────────────────────────
    (
        "tpl-cached-probe",
        (
            "CACHED_PROBE template — Engram pattern: payload-configured data monitor. "
            "Dual invocation: (1) periodic — check cache age, refresh if stale; "
            "(2) explicit — surface cached value immediately. Optional worry branch: "
            "if worry_after exceeded, escalate. Distinct from THRESHOLD_ALERT "
            "(age-based cache, not accumulation-based)."
        ),
        {
            "pattern_name": "CACHED_PROBE",
            "schema_version": 1,
            "substitution_engine": "jinja2",
            "slot_manifest": [
                {
                    "name": "probe_name",
                    "required": True,
                    "type_hint": "str",
                    "validator": {"pattern": r"^[a-z][a-z0-9_\-]+$"},
                },
                {
                    "name": "source_fn",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "trigger_phrase",
                    "required": True,
                    "type_hint": "str",
                },
                {
                    "name": "cache_ttl",
                    "required": False,
                    "default": 300,
                    "type_hint": "int",
                    "validator": {"min": 1, "max": 86400},
                },
                {
                    "name": "worry_after",
                    "required": False,
                    "default": 0,
                    "type_hint": "int",
                    "validator": {"min": 0, "max": 86400},
                },
                {
                    "name": "worry_fn",
                    "required": False,
                    "default": "",
                    "type_hint": "str",
                },
            ],
            "expansion_schema": [
                {
                    "id": "proc_probe_{{ probe_name | snake }}_check",
                    "habit_type": "threshold",
                    "name": "PROC_PROBE_{{ probe_name | upper | replace('-', '_') }}_CHECK",
                    "trigger": "heartbeat_tick",
                    "narrative": (
                        "CACHED_PROBE check: {{ probe_name }} — on heartbeat, check cache age; "
                        "if >{{ cache_ttl }}s: refresh via {{ source_fn }}"
                    ),
                    "metadata": {
                        "habit_type": "threshold",
                        "trigger": "heartbeat_tick",
                        "code_ref": "{{ source_fn }}",
                        "cache_ttl": "{{ cache_ttl }}",
                        "worry_after": "{{ worry_after }}",
                        "worry_fn": "{{ worry_fn }}",
                        "probe_name": "{{ probe_name }}",
                        "phase": "check",
                        "pattern": "CACHED_PROBE",
                        "tags": ["cached_probe", "monitor"],
                        "description": (
                            "Periodic cache-age check for {{ probe_name }}; "
                            "refresh via {{ source_fn }} when >{{ cache_ttl }}s stale"
                        ),
                    },
                },
                {
                    "id": "proc_probe_{{ probe_name | snake }}_surface",
                    "habit_type": "reactive",
                    "name": "PROC_PROBE_{{ probe_name | upper | replace('-', '_') }}_SURFACE",
                    "trigger": "{{ trigger_phrase }}",
                    "narrative": (
                        "CACHED_PROBE surface: {{ probe_name }} — explicit invocation, "
                        "surface cached value immediately"
                    ),
                    "metadata": {
                        "habit_type": "reactive",
                        "trigger": "{{ trigger_phrase }}",
                        "code_ref": "{{ source_fn }}",
                        "cache_ttl": "{{ cache_ttl }}",
                        "probe_name": "{{ probe_name }}",
                        "phase": "surface",
                        "pattern": "CACHED_PROBE",
                        "tags": ["cached_probe"],
                        "description": (
                            "On '{{ trigger_phrase }}': surface cached {{ probe_name }} value"
                        ),
                    },
                },
            ],
            "instantiation_contract": {
                "produces": ["threshold", "reactive"],
                "condition_signature": (
                    "trigger='heartbeat_tick' | '{{ trigger_phrase }}'"
                ),
                "invariants": [],
                "edge_policy": "generate_fresh",
            },
        },
    ),
]


# ── Seed runner ────────────────────────────────────────────────────────────────


def seed():
    cortex = get_cortex()
    seeded = []
    skipped = []
    errors = []

    for template_id, narrative, schema in TEMPLATES:
        existing = cortex.get(template_id)
        if existing:
            skipped.append(template_id)
            continue

        mem = Memory(
            id=template_id,
            narrative=narrative,
            memory_type=MemoryType.PROCEDURAL,
            metadata={
                "template_schema": schema,
                "tags": ["template", "engram"],
            },
            source="user_seeded",
            context_of_encoding=(
                f"T-template-seed-patterns: Engram {schema['pattern_name']} pattern"
            ),
            confidence=1.0,
        )
        try:
            cortex.store(mem)

            # Verify round-trip
            stored = cortex.get(template_id)
            assert stored is not None, f"node {template_id} not found after store"
            assert (
                stored.metadata.get("template_schema", {}).get("pattern_name")
                == schema["pattern_name"]
            ), f"template_schema not preserved for {template_id}"
            seeded.append(template_id)
        except Exception as e:
            errors.append((template_id, str(e)))

    print(f"\nEngram template seeding complete")
    print(f"  Seeded:  {len(seeded)}")
    print(f"  Skipped: {len(skipped)} (already present)")
    print(f"  Errors:  {len(errors)}")
    if seeded:
        print("\nSeeded:")
        for tid in seeded:
            print(f"  + {tid}")
    if skipped:
        print("\nSkipped (already present):")
        for tid in skipped:
            print(f"  = {tid}")
    if errors:
        print("\nErrors:")
        for tid, err in errors:
            print(f"  ! {tid}: {err}")
        sys.exit(1)

    print("\nVerify with Igor: list_templates()")


if __name__ == "__main__":
    seed()
