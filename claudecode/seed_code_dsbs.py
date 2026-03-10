#!/usr/bin/env python3
"""
seed_code_dsbs.py — Store DSB (Distilled Semantic Block) summaries of Igor's
key source modules as tagged blobs in his memory DB.

Run once (or re-run to refresh). Tags: code_summary, dsb, <module_name>, startup
Igor can retrieve at boot: cortex.search_by_tags(["code_summary"]) for fast map.

Usage: python claudecode/seed_code_dsbs.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

import os
env_path = Path.home() / ".TheIgors" / "igor_wild_0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ.get(
    "IGOR_DB_PATH",
    Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"
))

# ── DSB definitions ───────────────────────────────────────────────────────────
# Format: (module_path_rel, tags, narrative, dsb_content)

DSBS = [
    (
        "igor/main.py",
        ["code_summary", "dsb", "main", "startup", "boot", "routing"],
        "DSB: main.py — Igor main loop, boot sequence, tier ladder",
        """\
[DSB|module=main.py|lines=2390|claude-code|2026-03-05]

CLASS: Igor — central agent class.

BOOT SEQUENCE (Igor.__init__):
  DB open → genesis/integrity_check → NE/reasoner/thalamus init
  → discord_bot/net_listener/web_server/boot_check.start()
  → _export_portable_identity() → build_boot_message() → SESSION_START ring write
  _boot_ready=False until run() pre-warms system_prompt cache → set True

MAIN LOOP (Igor.run()):
  Pre-warm system_prompt → stdin_queue thread → while True:
    stdin first (commands responsive) → _drain_network() → run_background_sources()
    → _run_ne_background() → _drain_job_completions() → time.sleep(0.5)

TIER LADDER (_reason_with_failover):
  tier.1: habit match (basal_ganglia.select_habit)
  tier.2: KoboldCpp/Llama-3.2-1B — local, NE/impulses only; interactive skips
  tier.3: OR cheap (gpt-4o-mini) — background/preparse only
  tier.3.5: OR interactive (deepseek-chat) — human turns
  tier.4: OR claude (claude-sonnet-4-6)
  tier.5: Anthropic direct
  tier.6: arbiter alert (all upstreams failed)

COMPLEXITY GATE: compute_complexity() score>0.6 → skip to tier.4

KEY FLAGS: _boot_ready, _context_flush_done, _consecutive_impulse_failures
KEY ENV: IGOR_DB_PATH, IGOR_SELF_EDIT_ENABLED, IGOR_LOCAL, OPENROUTER_API_KEY
""",
    ),
    (
        "igor/memory/cortex.py",
        ["code_summary", "dsb", "cortex", "memory", "startup"],
        "DSB: cortex.py — SQLite memory graph, search, blobs, ring, TWM",
        """\
[DSB|module=memory/cortex.py|lines=829|claude-code|2026-03-05]

CLASS: Cortex — all persistent memory. Thread-safe via per-call connections.

TABLES: memories, ring_memory (FIFO-50), twm_observations (+urgency REAL 0.2),
        memory_blobs (tagged reference docs)

KEY METHODS:
  store(Memory) → upsert by id, scrubs metadata strings
  search(query, limit) → hybrid: text Phase1 → cosine rerank Phase2 (nomic-embed-text)
    → sets m.relevance_score
  write_ring(content, category) → FIFO-50 short-term context
  twm_push(source, content_csb, salience, urgency, ttl_seconds) → TWM observation
  twm_extend_ttl(obs_id, seconds, reason) → Signals A/B/C
  store_blob(narrative, content, tags) → REFERENCE memory + memory_blobs row
  get_blob(memory_id) / search_by_tags(tags) → blob retrieval
  count_by_type() → dict[type→count] for dashboard
  integrity_check() → verifies CP1-CP6 graph at boot

EMBEDDING CACHE: ~/.TheIgors/cache/embeddings/<sha256>.json
LAZY MIGRATION: embedding column added on first access if absent
_safe_memory_type(): catches ValueError, falls back to FACTUAL
""",
    ),
    (
        "igor/cognition/narrative_engine.py",
        ["code_summary", "dsb", "narrative_engine", "ne", "startup"],
        "DSB: narrative_engine.py — NE daemon, TWM integration, memory promotion",
        """\
[DSB|module=cognition/narrative_engine.py|lines=532|claude-code|2026-03-05]

CLASS: NarrativeEngine — background coherence daemon.

TRIGGER: 5+ unintegrated TWM obs OR 5-min timeout. Runs in ne-worker daemon thread.
MODELS: KoboldCpp first → Ollama gemma3:1b fallback. NE timeout=120s.
NE IMPULSES: local only (never cloud per D032).

CYCLE (_run_cycle):
  Load unintegrated TWM obs → _cap_observations() → _build_prompt()
  → local LLM call → _parse_ne_json() → _apply_output()

_apply_output:
  1. Update salience per salience_updates
  2. Mark obs integrated
  3. Promote memory_candidates (importance>0.7) to LTM via cortex.store()
  4. Write narrative fragment to ring(category=narrative)
  5. Queue action_impulses → main loop

MEMORY TYPE GUIDANCE (fb25354):
  episodic=one-time event | interpretive=meaning/insight
  procedural=recurring pattern or HOW TO | factual=stable reference

SELF-REF GUARD (WO7): NE must not generate content about its own process.
FORENSIC LOG: ~/.TheIgors/logs/ne_runs.log — promoted/impulses/elapsed per run
""",
    ),
    (
        "igor/cognition/reasoners/anthropic.py",
        ["code_summary", "dsb", "anthropic", "reasoner", "startup"],
        "DSB: anthropic.py — Claude API tool loop, rate limiting, auto-Haiku",
        """\
[DSB|module=cognition/reasoners/anthropic.py|lines=394|claude-code|2026-03-05]

CLASS: AnthropicReasoner(ClaudeFamily) — primary reasoning engine.

TOOL LOOP:
  Build system_prompt (SHA-256 cached) → prepend preparse_csb → API call
  → for each tool_use block:
      1. Rate limit check (TurnRateLimiter — #82)
      2. Auto-Haiku switch on self-edit tools
      3. registry.execute(tool_name, input)
      4. record() + forensic log
      5. _cap_tool_result(str(result)) — TOOL_RESULT_MAX_CHARS=20k
  → loop until stop_reason=end_turn or MAX_TURNS=25

RATE LIMITS (rate_limiter.py, #82):
  read_file×10, list_directory×5, run_bash×5, total=20/turn

AUTO-HAIKU: self-edit tools (list/read/patch/edit_source_file) → model=claude-haiku-4-5
Signal B: high valence memory → extend TWM TTL 1800s
Ethics gate: validate_against_core violation → arbiter urgency=0.9

CONTEXT MANAGEMENT:
  CONTEXT_WARN_CHARS=100k → yellow warning
  CONTEXT_HARD_CAP_CHARS (trim) → _trim_messages()
""",
    ),
    (
        "igor/tools/self_edit.py",
        ["code_summary", "dsb", "self_edit", "tools", "startup"],
        "DSB: self_edit.py — Igor self-modification tools with inertia gate",
        """\
[DSB|module=tools/self_edit.py|lines=514|claude-code|2026-03-05]

INERTIA MAP (hardcoded):
  brainstem/=0.95(WRITE_EXCLUDED), memory/models.py=0.95, reasoners/base.py=0.90
  memory/cortex.py=0.75, prefrontal_cortex.py=0.75, anthropic.py=0.70
  thalamus.py=0.50, main.py=0.50, tools/=0.30, dashboard/=0.30

WRITE GUARDS (checked in order for patch/edit):
  1. IGOR_SELF_EDIT_ENABLED=false → blocked (log to blocked_edits.log)
  2. brainstem/ path → hard blocked (WRITE_EXCLUDED)
  3. inertia>=0.90 (HIGH) → submit to arbiter queue, return BLOCKED (#69)
  4. syntax check → reject on SyntaxError
  5. backup .bak → write → git commit+push

TOOLS: list_source_files, read_source_file, edit_source_file,
       patch_source_file (preferred for <50 lines), run_syntax_check
SOURCE_ROOT: wild_igor/igor/ (sandbox — escaping raises PermissionError)
FORENSIC LOG: ~/.TheIgors/logs/self_edit.log
""",
    ),
    (
        "igor/cognition/system_prompt.py",
        ["code_summary", "dsb", "system_prompt", "startup"],
        "DSB: system_prompt.py — system prompt builder with SHA-256 cache",
        """\
[DSB|module=cognition/system_prompt.py|claude-code|2026-03-05]

FUNCTIONS:
  build_system_prompt(cortex, instance_id) → str
    3 layers: CHARACTER (CP/ID/PROC memories) → ORIENTATION POINTER → SAFETY-CRITICAL NOTES
    SHA-256 cached in _cache dict. invalidate_cache() clears on memory writes.
    Pre-warmed at top of Igor.run() to avoid cold first turn.

  build_boot_message(cortex, instance_id, warm_context) → str
    Synthetic first-turn orientation. Injected to ring + TWM (sal=0.9, urg=0.9, ttl=1800).
    Reads boot_notes.md from ~/.TheIgors/igor_{id}/boot_notes.md

  invalidate_cache() → called after _pre_compaction_flush() and _arbiter_resolve()

PERSONA RULES: no "I'm just an AI" / "I don't have feelings" / assistant-speak
CP5: inner-state language allowed and encouraged
""",
    ),
    (
        "igor/cognition/milieu.py",
        ["code_summary", "dsb", "milieu", "cognition", "startup"],
        "DSB: milieu.py — ambient affect state (valence/arousal/dominance)",
        """\
[DSB|module=cognition/milieu.py|claude-code|2026-03-05]

CLASS: MilieuState — 3D affect vector, all dims in [-1,1].
  valence (negative↔positive), arousal (calm↔activated), dominance (low↔high agency)

DYNAMICS: asymmetric EMA — α_up=0.25 (fast rise), α_down=0.05 (slow decay)
  Each tick: state × 0.98 (decay toward neutral). Persists to milieu.json.

MilieuSource: pushes state to TWM every 60s (salience=0.4)
MilieuInterruptor: fires when arousal>0.7 OR valence<-0.5

INTEGRATION:
  basal_ganglia uses arousal to modulate habit threshold (high arousal → lower threshold)
  NE _apply_output calls ingest_ne_state(internal_state) to update from LLM output
  milieu_mod.init(instance_id) / milieu_mod.get() → module singleton
""",
    ),
    (
        "igor/cognition/basal_ganglia.py",
        ["code_summary", "dsb", "basal_ganglia", "habits", "startup"],
        "DSB: basal_ganglia.py — parallel habit scoring, winner-take-all",
        """\
[DSB|module=cognition/basal_ganglia.py|claude-code|2026-03-05]

FUNCTION: select_habit(parsed, habits, milieu_state) → (Memory|None, float)
  Scores all habits in parallel; returns (winner, confidence) or (None, 0.0).

SCORING per habit:
  trigger_score = 1.0 if trigger in parsed.raw.lower() else 0.0 (filters non-matches)
  keyword_bonus ≤0.15 (overlap with parsed.keywords)
  activation_bonus ≤0.15 (habit.activation_count × 0.003, caps at 50)
  inertia_bonus ≤0.10 (habit.inertia × 0.10)
  valence_bonus ≤0.10 (habit.valence × 0.10)

THRESHOLD: BASE=0.50, modulated by milieu:
  high arousal → lower threshold (more reactive)
  low dominance → higher threshold (less confident)
  clamped [0.30, 0.70]

COMPILE PHRASES: "build a habit", "whenever ", "from now on" etc.
  → returns (PROC_HABIT_COMPILER, 0.95) immediately (pre-check)

RING LOG: HABIT_TRIGGERED|id=X|score=X.XX|trigger=Y
""",
    ),
]


def main():
    print(f"Connecting to {DB_PATH}...")
    cortex = Cortex(DB_PATH)

    existing = cortex.search_by_tags(["code_summary", "dsb"])
    existing_narratives = {r["narrative"] for r in existing}

    created = 0
    skipped = 0
    for module_path, tags, narrative, content in DSBS:
        if narrative in existing_narratives:
            print(f"  skip (exists): {module_path}")
            skipped += 1
            continue
        mem = cortex.store_blob(
            narrative=narrative,
            content=content,
            tags=tags,
            parent_id="CP3",
            valence=0.3,
        )
        print(f"  stored {mem.id[:8]}: {module_path}")
        created += 1

    print(f"\nDone. Created={created} Skipped={skipped}")
    print("Igor can retrieve with: cortex.search_by_tags(['code_summary'])")


if __name__ == "__main__":
    main()
