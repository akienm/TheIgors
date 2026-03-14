# Igor — Key Design Decisions

*Updated: 2026-03-14 | Full decision log (D001–D060): `design_docs_for_igor/decisions_log.dsb`*

This document covers the decisions that shape how Igor works at the broadest level — the ones that matter most if you're reading the code, debugging a behavior, or proposing a change.

---

## Foundational

**D001 — Everything is memory**
No special cases. Habits are PROC memories. Values are high-inertia memories. Everything is connected and evolvable through the same graph.

**D002 — Brain region naming**
Cortex, thalamus, basal ganglia, etc. are functionally accurate, not metaphorical. Each module does what the biological region actually does.

**D004 — SQLite, not JSON**
SQLite survives crashes. Atomic writes. Queryable. JSON files corrupt silently and can't be queried. All memory storage moved to SQLite.

**D005 — Inertia from network position**
Inertia is computed from graph position, activation count, and dependency depth. It's not manually assigned — it emerges from use.

**D006 — CSB/DSB format**
Pipe-delimited key:value for design docs. Human + machine readable without parser overhead. DSB (Distilled Structured Block) is the machine-optimized variant (~80% token reduction vs. markdown).

**D007 — Push-based TWM**
Transient Working Memory is push-only: sources deposit, NE and reasoners pull. Decouples producers from consumers. TTL cleans up automatically.

---

## Architecture

**D012 — Haiku for self-edits**
Self-edit and debug operations always use Haiku regardless of `IGOR_MODEL`. Frequent code ops need cost reduction, not quality.

**D015 — Gateway pattern**
All inference routing lives in `inference_gateway.py`. Policy in one file, not scattered across 5. Visible via `describe()`.

**D016 — Arbiter queue**
File-backed JSON queue for irreversible actions. Human approves before Igor acts. Currently disabled (`IGOR_ARBITER_ENABLED=false`).

**D017 — Hybrid embedding search**
Text keyword scan → embedding rerank. Phase 1 always works. Phase 2 improves ranking when Ollama is up. Graceful degradation.

**D035 — Interactive persona tier**
All interactive turns land at tier.3.5 minimum (haiku), regardless of complexity. t2/t3 are background-only. This preserves Igor's persona in conversation — mechanical routing (t3) is fine for background impulses, not for direct conversation with Akien.

**D036 — Milieu**
3D affect (valence/arousal/dominance). Asymmetric EMA: fast rise (α=0.25), slow fall (α=0.05). Dominance baseline +0.3. Shapes habit thresholds and escalation.

**D037 — Basal ganglia**
Parallel scoring replaces first-match-wins. Milieu modulates threshold. Lateral inhibition. Score= in ring entries = audit trail.

---

## Session / Context

**D020 — Portable identity**
SOUL.md (CP1-CP6) and IDENTITY.md (ID1-ID14) are written every boot from the DB. They never drift from DB state. SOUL.md is shared across instances; IDENTITY.md is instance-scoped.

**D022 — Warm context**
TWM + ring_tail + NE state are serialized at shutdown and reloaded at boot (TTL=4h). Rotation .0→.1 prevents corruption on hard kill.

**D027 — TWM TTL extension**
TTL extends on confirmed usefulness, not mere access. Three signals: NE promotes (A), positive response valence (B), high cosine relevance (C).

**D028 — TWM urgency**
Urgency is orthogonal to salience. Urgency×salience sorts the NE queue. Urgency≥0.7 flagged distinctly in context.

---

## Inference

**D033 — CSB preparse**
`[PARSED_INPUT]` CSB block forwarded to cloud reasoners. LLM preparse is toggleable without changing routing logic. max_tokens=120, timeout=8s.

**D034 — Speed optimizations**
Fast-path skips LLM for greetings/commands (<1ms). Parallel preparse+search via ThreadPoolExecutor. HTTP keep-alive for KoboldCpp.

**D053 — NE response format JSON**
NE OpenRouter calls include `response_format: json_object`. Eliminates prose-wrapping parse failures that were silently dropping NE cycles.

---

## Self-Programming

**D040 — Hot module reload**
`importlib.reload()` on stateless leaf modules. HIGH inertia blocked. Tool modules self-re-register. No restart needed for leaf patches.

**D041 — Stateless by design**
Hot-reloadable modules hold no state (state lives in DB). `__class__` swap for edge cases. Cortex is the only stateful owner.

**D042 — DSB format**
Distilled Structured Block replaces CSB for machine-facing docs. ~80% token reduction. DSB loads directly into system prompt CHARACTER layer.

---

## Learning / Reading

**D047 — Learn-about tool**
`tools/learner.py`; "go learn about X tonight" habit. Calibre non-fiction filter. Browser AI discovery. `tonight` → queue. All background runs use local Ollama (free).

**D056 — Curriculum language first**
Learning order: language → cognitive science → how-Igor-works → programming/AI → culture. Language first because the word graph IS a language model.

---

## Session Operations (Meta)

**D058 — Skills as compiled exec functions**
Claude Code skills (`/savestate`, `/workstep`, `/igor`, `/validate-files`) are compiled executive functions — same architectural role as Igor's PROC nodes. They reduce working-memory load on Claude per session.

**D060 — Research delegation to Igor**
Bulk fact-gathering is delegated to Igor at tier.3 (gpt-4o-mini, ~10-50× cheaper). Output = topic DSB in `design_docs_for_igor/research/`. Claude reads the result for synthesis.
Decision tree: synthesis → Claude; gathering → Igor.
