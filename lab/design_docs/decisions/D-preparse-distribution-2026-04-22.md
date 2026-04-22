---
id: D-preparse-distribution-2026-04-22
title: Preparse distribution — atomic chunker + capacity profiler + router
date: 2026-04-22
status: open
spawned_tickets:
  - T-input-chunker
  - T-cluster-router-capacity-profile
  - T-preparse-router
---

# D-preparse-distribution-2026-04-22

## Decision

Preparse becomes a distributed scheduler with capacity-aware routing. Atomic input chunker splits long/multi-intent input into sentence-level units; per-machine capacity profile (sliding-window stats layer on cluster_router) learns safe input ceilings; preparse router groups atoms into machine-sized batches and dispatches in parallel via the existing inference_gateway. Gated on D-preparse-architecture-2026-04-22 for broader operational-model commitments (non-terminal emission, confidence-gated depth, gist-before-retrieve, tutor-not-oracle, shadow-stream scoped to reasoning).

## Context

Web-LLM preparse (gpt5mini) was previously removed from akiendell/akiendelllinux (T-pipeline-arch close note: "preparse removed entirely"). The replacement architecture needs to be LOCAL-first — graph-tree gist-pass as primary, local mini-LLM as fallback, no cloud round-trip on the critical path. Akien has observed that long conversational input borks preparse timeouts and multi-intent input (greeting + question + meta-comment in one message) gets muddled classification.

Local graph-tree preparse is expected to be 10–100× faster than the former web-LLM round-trip (10–50ms vs 500–2000ms). With per-machine capacity profiling we can route atomic chunks to whichever machine(s) are available and capable — the capacity profiler doubles as a general-purpose telemetry primitive reusable for reasoning dispatch.

## Spawned tickets

- **T-input-chunker** (S) — atomic splitter (sentences, discourse markers, clause fallback, paragraph boundaries). Pure function, reusable everywhere. No routing awareness.
- **T-cluster-router-capacity-profile** (M) — extend existing cluster_router.py with sliding-window per-machine latency-by-size stats; query API for safe_ceiling, p50_latency, is_overloaded.
- **T-preparse-router** (M, gated on above two) — group atoms into machine-sized batches, parallel dispatch, fallback chain (smaller groupings → local mini-LLM → graph-tree-only-with-low-confidence-flag), record outcomes back to capacity profile.

## Non-goals

- Cloud LLM fallback (explicitly excluded — local-first architecture).
- Cross-machine gossip sync of capacity stats (follow-on; per-caller view sufficient for MVP).
- Persistence of capacity stats to DB (follow-on; in-memory sliding window sufficient).
- Shadow-stream comparison on preparse (low-value per design — shadow is scoped to reasoning in D-preparse-architecture).

## Review context

Blanket pre-approval from Akien 2026-04-22 for HIGH-inertia touches implied by T-preparse-router's main.py integration. Approval covers the wider D-preparse-architecture batch filed the same day.
