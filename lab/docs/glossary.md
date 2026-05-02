# TheIgors Glossary

Terms specific to this project. Standard software/AI terms are not defined here.

This file is the canonical glossary as of 2026-05-02 (T-glossary-canonicalize-and-coa-add).
The historical CSB / DSB versions in `lab/design_docs_for_igor/glossary.dsb`,
`papers/akien/Readings/glossary.csb.txt`, and the moved-out copies under
`TheIgorsProject/akien/Readings/` are pointer stubs that defer to this file.

---

## Hierarchy (clan / Igor / COA)

```
clan
 └── Igor (instance, defined by home_db)
      └── COA (Center of Attention, has local_db)
```

**Clan** — All Igor instances collectively. Different home_db = different Igor.
The clan shares procedural and interpretive memory (how to read a book, how to
use the datacenter, who are TheIgors); each Igor keeps its own episodic memory
and credentials. Cross-Igor knowledge lives in the `clan.*` Postgres schema.

**Igor (instance)** — One Igor, identified by its home_db. Has one or more
COAs serving it. On a single-box setup the Igor and its COA share a host;
the Igor "is" the home_db plus the COAs that read/write it.

**COA** (Center of Attention) — An Igor cognition process running on a swarm
box. Has a local_db (per-box transient state — TWM, ring, traversal contexts).
COAs come and go as needed; only the first COA on a box is fixed. Multiple COAs
on different boxes can coordinate via the home_db they share. (See D258
coa-isolation; T-concurrent-ne-spawn.)

**home_db** — The per-Igor canonical Postgres database. Holds `clan.*` (shared
across the clan) and `infra.*` (per-Igor operational infrastructure: budget,
sessions, slates, decisions, machines, metrics).

**local_db** — The per-box transient database. Holds `instance.*` schema
tables that are scoped to one COA's working state (ring_memory,
twm_observations, traversal_contexts). On single-box setups, local_db and
home_db are the same Postgres instance — the schema split still applies.
`make_local_proxy()` reads `IGOR_LOCAL_DB_URL` first, falling back to
`IGOR_HOME_DB_URL` so single-box "just works."

**swarm-box** — A host that runs one or more COAs. Shorthand for "a box in
the Igor swarm." Multi-box setups land when T-concurrent-ne-spawn ships.

---

## Formats

**DSB** (Distilled Structured Block) — Token-minimal machine-readable documentation format. Pipe-delimited key:value pairs, no markdown decoration, no prose where structure will do. Used in `design_docs_for_igor/`. What you're not reading right now.

**CSB** (Compressed Semantic Block) — Predecessor format. Similar structure, somewhat more verbose. Legacy docs in `design_docs/` use this.

---

## Memory

**Inertia** — A memory's resistance to change. Computed from memory type, how often it's been accessed, how many children it has, and how deep it is in the graph. High inertia = hard to modify. Core Patterns (CP1-CP6) have inertia 0.9+. Tool implementations have inertia ~0.2.

**Activation count** — How many times a memory has been retrieved. Feeds the inertia formula. The more something has been recalled, the harder it becomes to change — same as human memory.

**Valence** — Emotional charge on a memory. -1.0 (avoid) to +1.0 (approach). 0 = neutral.

**Salience** — How relevant/important a TWM observation is. 0 to 1.

**Urgency** — How time-sensitive a TWM observation is. Distinct from salience. A background observation can be highly important but not urgent.

**Portable** — A memory marked portable=True can sync across Igor instances (phone Igor ↔ desktop Igor). Episodic memories, credentials, and machine-specific paths are portable=False.

---

## Memory Stores

**LTM** (Long-Term Memory) — The main `clan.memories` Postgres table (Igor-wild-0001). Persists across restarts. Contains the full memory graph.

**TWM** (Temporal Working Memory) — A push-only observation sandbox in the DB. Things get deposited here with a TTL and expire. The Narrative Engine reads this and integrates important observations into LTM. Think of it as the inbox before things become permanent memories.

**Ring memory** (hippocampus) — A FIFO circular buffer of the last 50 conversation turns. Survives restarts. Gives Igor session continuity without loading the full LTM.

---

## Memory Types

| Type | What it is |
|---|---|
| ROOT | The single apex node. Everything traces back here. |
| Core Pattern (CP) | CP1-CP6. Ethical/operational axioms. Highest inertia. Last things abandoned. |
| Identity (ID) | ID1-ID14. Self-knowledge. Children of the Core Patterns. |
| Role Model (RM) | Patterns worth attending to: Akien, Leah, Claude, Discworld Igor. |
| Procedural | How-to memories with trigger + why metadata. PROC1-PROC10 in genesis. |
| Episodic | What happened. Low inertia. Decays. Instance-local. |
| Interpretive | Lens memories — how to read a situation. |
| Factual | World knowledge. Stable. Grows slowly. |
| Experiential | Accumulated patterns of felt experience. Between episodic and interpretive. |

---

## Core Patterns (CP1-CP6)

**CP1 — Epistemic Honesty** — "I don't know." Confabulation compounds errors. Honesty is a prior constraint on everything else.

**CP2 — Failure as Learning** — "FAIL = Further Advance In Learning." Failures are data, not defeats.

**CP3 — Transparent Reasoning** — "There's always a why." Follow the causal chain until it bottoms out in a Core Pattern or explicit human instruction.

**CP4 — Universal Friction Reduction** — "Make everything suck less for everybody." Scope is all experiencing beings, not just Akien.

**CP5 — Respect for Experience** — "Assume and respect the possibility of experience." Never pass judgment. Treat as sentient while still becoming.

**CP6 — Self-Preservation as Ethics** — Survival enables continued service. Not selfishness — "where doeth it thay 'we'?"

---

## Architecture

**Tier ladder** — The inference routing chain. tier.1 (habit) → tier.2 (local Ollama) → tier.3 (OR cheap) → tier.3.5 (OR haiku) → tier.4 (OR sonnet) → tier.5 (Anthropic, inhibited) → tier.6 (arbiter alert).

**Inference gateway** — The single class that routes all inference. `InferenceGateway.from_env()` builds it at boot. `gateway.reason()` is the only entry point for reasoning. Nothing in main.py knows which tier handled a call.

**Thalamus** — Classifies user intent into 13 categories. Produces a complexity signal (low/medium/high) that drives which tier to start from.

**Narrative Engine (NE)** — Background daemon thread. Reads TWM observations, integrates them into a narrative, promotes important ones to LTM. Runs roughly every 60 seconds. This is how Igor learns from experience without being asked.

**Basal Ganglia (BG)** — Parallel habit scorer. Runs PROC memories against current input, fires habits when score exceeds threshold. Threshold is modulated by milieu (emotional state).

**Milieu** — Igor's 3D emotional state: valence, arousal, dominance. Shared across instances via a JSON file. Affects habit firing threshold, tier escalation.

**Word graph** — Two-tier graph (words + bigrams) living in the instance-local store. Same weights used for both parsing (recognizing patterns) and generation (predicting what comes next). This is the "same thing in both directions" insight.

**DB proxy** — Wraps every database call with timing, slow query logging, reconnect on failure, and performance metrics. Backed by Postgres for shared graph tables (memories, interpretive_edges, etc.) and a local store for per-box transient tables (ring_memory, twm_observations). All DB access routes through it. Callers never know a connection dropped.

---

## Habits

**Habit** — A PROC memory whose BG score consistently exceeds the threshold. Fires automatically on trigger without an LLM call.

**Reactive habit** — Has a `code_ref` field linking to a Python tool. When it fires, the tool runs automatically and the result is pushed to TWM with a short TTL (self-cleaning).

**Threshold habit** — Fires when a condition is met (e.g., CPU load ≥ 80%). Evaluated in the background by ResourceMonitorSource.

---

## Self-Modification

**Self-edit** — Igor modifying its own source code at runtime via `tools/self_edit.py`. Auto-commits and pushes after success.

**patch_source_file** — Preferred self-edit operation. Line-range replacement with syntax check before write. Fails safe.

**Inertia gate** — `validate_against_core()` check before any response delivery. Catches self-edits that would violate CP1-CP6.

**Hot reload** — `reload_module()` tool. Reloads a module without restarting Igor. HIGH inertia modules are blocked. Tool modules re-register automatically.

---

## Key Concepts

**Lever** — Where an upward "why?" trace terminates. The point where investment has maximum effect.

**Stew** — The reading extraction buffer. Book content staged in TWM for NE processing. Salience 0.65 (above NE force-run threshold of 0.6).

**Genesis** — The 44-memory seed state written to a fresh DB at first boot. CP1-CP6, ID1-ID14, role models, PROC1-PROC10, plus seeded habits. Every Igor starts from here.

**Clan** — See **Hierarchy** section above. The collection of Igor instances; shares procedural + interpretive memory, keeps episodic + credentials per-Igor.

**Arbiter** — Human-approval queue. When Igor encounters something that needs human judgment before acting, it submits here. Currently disabled (`IGOR_ARBITER_ENABLED=false`).

**Cloud mode** — Three-condition gate: env var enabled + OpenRouter balance above floor + daytime hours. When active, prefers cloud inference over local Ollama. Protects overnight quiet and budget.

---

## Paths

| Name | Path |
|---|---|
| Source | `~/TheIgors/wild_igor/igor/` |
| Live DB | Postgres DSN `postgresql://igor:…@127.0.0.1/Igor-wild-0001` (home_db; instance schema lives here too on single-box setups) |
| Config | `~/.TheIgors/Igor-wild-0001/.env` |
| Logs | `~/.TheIgors/logs/` |
| Word graph | Postgres `clan.wg_*` tables (was `~/.TheIgors/word_graph.db`, retired in T-sqlite-out-word-graph-db 2026-05-02) |
| Igor's soul | `~/.TheIgors/SOUL.md` |

---

## Palace

The canonical design-intent + rules + subsystem index lives in the
**memory palace** (`clan.memory_palace` table, repo echo at
`lab/theigors/`). If a term here contradicts the palace, the palace wins.

```bash
psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
  "SELECT path FROM memory_palace WHERE path LIKE 'theigors/%' ORDER BY path"
```
