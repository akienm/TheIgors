# TheIgors Glossary

Terms specific to this project. Standard software/AI terms are not defined here.

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

**LTM** (Long-Term Memory) — The main `memories` SQLite table. Persists across restarts. Contains the full memory graph.

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

**Word graph** — SQLite-backed two-tier graph (words + bigrams). Same weights used for both parsing (recognizing patterns) and generation (predicting what comes next). This is the "same thing in both directions" insight.

**DB proxy** — Wraps every SQLite call with timing, slow query logging, reconnect on failure, and performance metrics. All DB access routes through it. Callers never know a connection dropped.

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

**Clan** — All Igor instances collectively. They share procedural and interpretive patterns but not episodic memories (those are personal).

**Arbiter** — Human-approval queue. When Igor encounters something that needs human judgment before acting, it submits here. Currently disabled (`IGOR_ARBITER_ENABLED=false`).

**Cloud mode** — Three-condition gate: env var enabled + OpenRouter balance above floor + daytime hours. When active, prefers cloud inference over local Ollama. Protects overnight quiet and budget.

---

## Paths

| Name | Path |
|---|---|
| Source | `~/TheIgors/wild_igor/igor/` |
| Live DB | `~/.TheIgors/Igor-wild-0001/wild-0001.db` |
| Config | `~/.TheIgors/Igor-wild-0001/.env` |
| Logs | `~/.TheIgors/logs/` |
| Word graph | `~/.TheIgors/word_graph.db` |
| Igor's soul | `~/.TheIgors/SOUL.md` |
