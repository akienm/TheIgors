---
id: D-preparse-architecture-2026-04-22
title: Preparse + reasoning operational-model redesign
date: 2026-04-22
status: open
spawned_tickets:
  - T-non-terminal-emission
  - T-salience-residue-scan
  - T-gist-before-retrieve
  - T-tutor-not-oracle-prompt
  - T-local-preparse-fallback
  - T-shadow-stream-reasoning
  - T-confidence-gated-depth-scoping
---

# D-preparse-architecture-2026-04-22

## Decision

Decompose Igor's input-to-reply pipeline into a 9-stage monkey-brain model (attend → predict → recognize → retrieve → reason → select → articulate → reflect → learn), with most stages replaceable by graph-tree operations and confidence-gated short-circuits. Six concrete implementation tickets plus one design-scoping ticket for the confidence-gated-depth principle which requires per-stage inventory before build.

## Context

Triggered by measured preparse latency (20–24s post-D-slow-query-triage) on trivial inputs like "hi". Initial proposal was a narrow reflex-intent memory-search skip. Akien rejected the narrow framing with "our graph trees should be able to do that" — the whole decision tree of when-to-retrieve, what-to-reason-about, how-to-select-output should be expressible as graph operations with LLM as fallback, not hardcoded conditionals.

Design decisions locked in:

**Non-terminal emission** — reply-sent ≠ turn-done. Reflex reply becomes a pursuit-child that completes fast while the parent pursuit resumes to scan for residual content. Matches monkey-brain "Hi! ... oh, and about X..." pattern. Reuses existing pursuit parent-child suspend/resume mechanism (D-pursuit-layer).

**Confidence-gated depth** — each stage emits a confidence score; next stage is gated on whether confidence clears a threshold. High → short-circuit; low → proceed to full processing. Principle touches every stage; scoped into per-stage tickets via T-confidence-gated-depth-scoping.

**Gist-before-retrieve** — graph-tree gist-pass (habit_list + hot_attractors + NE-predict) runs BEFORE cortex.search. Reflex intents (greeting, ack, farewell, command) short-circuit the retrieval stage entirely.

**Tutor-not-oracle** — when Igor calls an upstream LLM for reasoning assistance, the prompt asks for a thinking-frame ("what questions should he ask himself? what options is he missing?") not an answer. Forces Igor to apply the frame rather than copy output. Richer learning signal via reasoning-shape transfer.

**Shadow-stream scoped to reasoning** — parallel Igor-path + tutor-LLM-path, both live, first-confident-wins. Divergence recorded as training corpus. Scoped to reasoning only (preparse shadow is low-value — too much "NE was right about greeting again" noise for the compute cost). Articulation shadow is as-needed (when Igor's draft has low register/clarity confidence).

**Local-first** — no cloud round-trip on the critical path. Local mini-LLM (Ollama small-model) fills the middle tier between graph-trees and cortex.search. Matches Akien's explicit removal of gpt5mini preparse from akiendell/akiendelllinux.

## Spawned tickets

- **T-non-terminal-emission** (M, p=0.8) — reply-as-pursuit-child, parent-resumes for residue scan. HIGH-inertia main.py touch, pre-approved.
- **T-salience-residue-scan** (M, p=0.75, gated on T-non-terminal-emission) — "anything else interesting?" scan over unaddressed input; spawns continuation pursuit if high-salience content remains.
- **T-gist-before-retrieve** (S, p=0.85) — reorder preparse so graph-tree gist-pass precedes cortex.search; confidence-gated short-circuit for reflex intents. HIGH-inertia main.py touch, pre-approved.
- **T-tutor-not-oracle-prompt** (M, p=0.7) — change upstream LLM prompt shape from answer to thinking-frame.
- **T-local-preparse-fallback** (M, p=0.6, gated on T-gist-before-retrieve) — local Ollama mini-LLM fallback when graph-tree confidence is low.
- **T-shadow-stream-reasoning** (L, p=0.5, gated on T-tutor-not-oracle-prompt) — dual-path reasoning with first-confident-wins + divergence corpus for off-policy learning.
- **T-confidence-gated-depth-scoping** (S, p=0.4) — design-only; inventory per-stage confidence emission gaps and propose per-stage tickets.

## Non-goals

- Cloud LLM fallback anywhere on the critical path.
- Replacement of reasoning stage with pure graph operations (marked HARD; reasoning remains the stage where LLM assistance is most valuable).
- Training algorithm for divergence corpus (separate ticket once corpus exists).
- User-feedback labeling mechanism (needed eventually but not in this batch).

## Review context

Blanket pre-approval from Akien 2026-04-22 at 14:27 for the whole batch: "approved for huge batch sprint based on the priorities already discussed and your best judgement." Covers HIGH-inertia main.py touches in T-non-terminal-emission and T-gist-before-retrieve.

## Sibling decision

D-preparse-distribution-2026-04-22 handles the distributed dispatch layer (chunker, capacity profiler, router). Both decisions shipped the same day; they compose — distribution is the how-to-deliver, architecture is the what-to-deliver.
