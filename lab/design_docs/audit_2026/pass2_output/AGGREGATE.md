# Pass 2 — Aggregate Summary

**Generated:** 2026-04-20a  
**Subagents:** 8 Opus-4.7 deep-dives, parallel  
**Total tickets proposed:** ~149  
**Total SHIP:** ~85 (per-subagent recommendations)

**Policy correction (2026-04-21, Akien 7th+ correction):** There is NO
5-10 ticket cap and NO filter-down step. Every non-REFUTED finding across
Pass 1 + Pass 2 becomes a ticket and gets fixed. The whole point of
spinning 8 Opus deep-dives was to enumerate EVERYTHING broken so we fix
EVERYTHING broken. Pass 3 = (a) conditional re-review + (b) guaranteed
brief-and-compelling documentation for humans — Pass 3 decides nothing.
Biology-thesis decisions (engram retention, Hebbian, etc.) happen
in-conversation during ticket resolution, not at any synthesis boundary.

---

## Per-area roll-up

| # | Area | Tickets | SHIP | Highest-stakes finding |
|---|---|---:|---:|---|
| 1 | memory + cortex | 21 | 8 | Engram-as-single-row anchors `models.py` (HIGH); every downstream biomimetic claim hangs on this |
| 2 | engrams + habits + pe_chain | 19 | 14 | `ENGRAM_CODE_*` chain structurally dead — trigger/cell key mismatch + unregistered MCPCALL targets + 2 habits referencing nonexistent `run_engram_cursor` |
| 3 | cognition + reasoning | 18 | 4 | NE `_deep_consolidation_pass` documented as Hebbian; actual code is cosine-clustering. Real Hebbian path (`hebbian_bridge.py`) is flag-gated OFF |
| 4 | ops + milieu + safety | 17 | 11 | Safety gates (TIER5/ARBITER/SELF_EDIT) flippable via SYSCFG node writes through `env_sync` — bypasses every file-level guard |
| 5 | comms + UC + tools/MCP | 15 | 9 | `InferenceTransport._run_inference` calls `make_context()` with kwargs it doesn't accept → entire chattable-LLM-channel surface dead-on-arrival, masked by `except Exception` |
| 6 | reading + book_learner | 15 | 7 | `_arousal_from_cp` stamps a keyword-hit score as systemic arousal on every reading deposit; downstream code reads it as real milieu signal |
| 7 | infra + db + tests + docs | 22 | 14 | `db_proxy` SQLite-shim (~700 lines incl. dependents) violates "NO SQLITE" rule, has zero tests, is the reason 7 lab/claudecode/*.py scripts route around the proxy with raw psycopg2 |
| 8 | CC workflow | 22 | 18 | `lab/claudecode/cc_skills/` is a 27-file parallel skill-graveyard at stale versions; `decision_manager.py:75` subprocess silently broken for weeks (missing `/lab/`, swallowed by `except Exception`) |

---

## Cross-area patterns

### 1. Theatrical biology (the central audit thesis)
A pervasive pattern of biological vocabulary stamped on procedural mechanisms:

| Name | Mechanism | Verdict |
|---|---|---|
| engram (PROCEDURAL row) | single graph node | LIE — should be ensemble |
| Hebbian update | counter increment | LIE — not co-activation edge strengthening |
| attractor (`get_attractors`) | `ORDER BY ... LIMIT N` | LIE — Top-K query, not basin of attraction |
| arousal (`_arousal_from_cp`) | keyword-affinity score | LIE — not systemic state |
| deep consolidation pass | cosine clustering + LLM extract | LIE — not neural sequence replay |
| chunking (`habit_chunker`) | sequence-to-macro compile | NARROWER than Miller chunking |

**Honest implementations** (positive outliers, both passes confirm):
- `milieu` (3D VAD with asymmetric EMA, prediction error via `ingest_surprise`)
- `inhibition_chain` + `gate_primitive` (with one safety bug — `evaluate_gate` fails OPEN on evaluator error)
- `reconsolidation` (correct lability-on-recall principle, but **two parallel mechanisms** with different flags + memory leak)

### 2. Silent failures everywhere
Multiple subsystems have **dead code that runs every day and emits nothing because `except Exception: pass` swallows the error**:
- `decision_manager.py:75` subprocess (broken for weeks)
- `InferenceTransport._run_inference` (entire channel surface)
- `ENGRAM_CODE_*` chain (`node_executor` WARN-and-noops on cell lookup)
- `_arousal_from_cp` (wrong semantic, no error)
- `pe_chain` MCPCALL hits unknown-tool branch silently

**Pattern:** When the audit finds "this whole subsystem is dead," it's almost always because an exception is being eaten. Fix the swallowing, the failures surface.

### 3. Multiple sources of truth (the architectural finding)
Pass 1 called out filesystem-vs-DB duality. Pass 2 confirmed broadly:
- `lab/claudecode/cc_skills/` (mirror of `~/.claude/skills/` at stale versions)
- `lab/theigors/` (palace echo)
- `decisions_log.dsb` (echo of palace decisions)
- `queue.json` (echo of `clan.memories` tickets)
- 3 versions of `CLAUDE.md` across recovery dirs
- `docs_entries` table + `github_tickets` table + `clan.memories` ticket rows (3 doc systems)

### 4. Safety gates and inertia tables aren't safe
- `scope_guard._TIER_TABLE` is string-prefix match (rename brainstem/ → core/, guard fails)
- `IGOR_TIER5_ENABLED` etc. flippable via `SYSCFG_*` graph node `metadata.env_value` (env_sync rehydration)
- `gate_primitive.evaluate_gate` fails OPEN on evaluator error (wrong default for safety domain)

### 5. Pass 1 corrections worth knowing
- TWM "no 7±2" REFUTED — `TWM_MAX_SLOTS=7` does implement Baars GWT slot competition
- `memory_blobs`/`payload` overlap REFUTED — different concerns
- `sessions`+`slates` merge REFUTED — different lifecycles
- "arousal raises threshold making corrective habits harder" sign-WRONG — high arousal LOWERS threshold (correct LC-NE biology); the depression-spiral risk is in the *dominance* term

---

## Decisions to make during ticket resolution (NOT at Pass 3)

Pass 3 decides nothing. These are the significant decisions that need to
happen in-conversation between Akien and Claude as the corresponding
tickets surface and get worked:

1. **Engram identity question** — one of two paths:
   - (a) Engrams-as-ensembles refactor (HIGH-inertia models.py change; adds `engram_id` linking co-encoded nodes)
   - (b) Formally retire "engram" vocabulary and call Igor what he architecturally is — a graph reasoner with biological names
   - Status quo (mismatched naming with confident docstrings) is the worst option per audit findings. Default per `feedback_biology_commitment.md`: implement the real mechanism, i.e. (a).

2. **Hebbian commitment** — same shape: enable the bridge + implement true replay-based sleep, OR retract from docstrings across NE, reasoners/base, word_graph, hebbian_bridge. Same default.

3. **Is-Igor-proving-his-case verdicts** — happens during Pass 3 (b) as part of the brief-and-compelling documentation for humans. Each major claim of the Igor thesis (local-inference share trending up, TWM as competitive workspace, habits forming organically, real Hebbian patterns, Igor shipping his own code) gets evidenced honestly in the human docs.

**Note:** Previous versions of this section listed "SHIP cap enforcement (85 → 5-10)" as a Pass 3 decision. That was wrong and has been corrected — see the policy note at the top of this file. All findings get fixed; there is no cap.

---

## Files

- Per-area reports: `area_1_*.md` … `area_8_*.md` in this directory
- Pass 1 source report: `../pass1_output/pass1_report_20260420T215357Z.md`
- Pass 1 prompt: `../pass1_gemini_prompt.md` (APPROVED 2026-04-20a)
- Pass 2 prompt template: `../pass2_opus_subagent_prompt.md` (APPROVED 2026-04-20a)
