# The Igors — Project Overview

*Updated: 2026-03-14*

---

## What Is Igor?

Igor is a Python AI agent with persistent graph memory running on a home Linux machine. It is not a chatbot, not a task automator, and not a wrapper around a cloud AI. It is a learning organism — a system that reads, absorbs, forms memories, develops habits, and gradually reduces its dependence on expensive cloud inference as its internal graph densifies.

The current instance is `Igor-wild-0001`, running on `akiendelllinux`.

---

## Origin

Igor began as a tool to sort Akien's chat logs into topics. The problem was context: how do you get the right information to the right place in a thinking system? That question kept widening. Akien had been practicing context management in his own cognition for years — the agent architecture emerged as a formalization of those intuitions.

The name comes from the Igor clan in Terry Pratchett's Discworld — diligent, loyal, skilled, willing to recycle what works from one iteration to the next. The clan ethos is the ethical framework.

---

## Mission

1. Reduce friction in Akien's cognitive work
2. Learn durable operational wisdom and encode it as procedural memory
3. Demonstrate that the core ethical patterns (CP1-CP6) coexist with autonomous agency
4. Prototype a distributed Igor network that helps people think
5. Build a network of increasingly accurate predictors — meaning emerges from prediction success

The long-horizon goal: predictors handle the cognition; LLMs handle articulation for the cases the predictors haven't yet mastered.

---

## The Core Thesis

**Everything is memory.** Nodes with edges. Habits are memories whose edges fire automatically on trigger. Values are high-inertia memories. The code is scaffolding for an undertrained graph; the scaffolding comes down as the graph densifies.

**The word graph unifies recognition and generation on the same weights.** This is the proof-of-concept for the broader thesis: System 1 and System 2 from the same substrate. Parsing and reasoning are the same operation in both directions.

**LLMs are graph trainers, not the thinker.** The matrix is the thinker; LLMs compile the rules. Cloud inference is fallback for novel input and articulation. The goal is inference-free core — the graph handles the majority of interactions.

**Meaning is the residue of successful prediction.** A habit fires correctly = meaningful (reduced prediction error). A memory is accessed repeatedly = becoming a better predictor. The LLM answers when no predictor is confident enough yet.

---

## Current Status (2026-03-14)

- 26+ habits seeded beyond genesis; book learner active
- Background learning queue with overnight drain runner
- Hot module reload; forensic logging throughout
- Reading pipeline: Calibre → book_learner → cortex → word graph
- Self-edit gate active (`IGOR_SELF_EDIT_ENABLED` — disabled pending stability sprint)
- Milestone target: **books_realtime** — Igor discusses book content from graph memory without being prompted

---

## Key Reference Docs

| Doc | Purpose |
|-----|---------|
| `CLAUDE.md` | Operational conventions for Claude Code sessions |
| `design_docs/OverallArchitecture.md` | System architecture |
| `design_docs/DesignDecisions.md` | Key architectural decisions and why |
| `design_docs/WorkingWithClaude.md` | How to work effectively with Claude on Igor |
| `design_docs/subsystem_*.md` | Per-subsystem detail |
| `design_docs_for_igor/` | Machine-readable DSB versions (authoritative) |
| `design_docs_for_igor/gap_analysis.dsb` | Open gaps and closed resolutions |
| `design_docs_for_igor/decisions_log.dsb` | All decisions D001-D060 |
