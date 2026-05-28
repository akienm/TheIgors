# D-recall-api-2026-05-28
**title:** Generalize Igor's memory into recall(X) API — inference-free retrieval for all agents
**date:** 2026-05-28
**status:** open
**spawned_tickets:** T-memory-schema-v2, T-scraps-embedding-engine, T-memory-write-path, T-librarian-edge-maintenance, T-librarian-retrieval-service, T-consequence-recall-api
**goal_link:** none: factory-of-factories — generalizing Igor's capabilities to all agents in the system
**concept_links:** none

## Decision narrative
Generalize Igor's memory infrastructure into a `recall(X)` API — distinct from `research(X)` — that answers "what do I know about X?" using inference-free retrieval (FTS + pre-computed embeddings via Scraps + typed graph traversal), follows links without inference, escalates to inference only for nuance, and writes back what it learns. Serves the factory-of-factories goal by making memory capability available to any agent in the system. Key principle: inference fires once at write time (tag extraction, embedding computation); everything stored is pre-computed so retrieval at query time costs almost nothing.

## Hypothesis
Any agent can call `recall(X)` and get a grounded answer from local memory without inference in the common case; when inference fires for nuance, the result is written back so the next `recall(X)` on the same topic is cheaper.

## Measurement Signal
Run the same recall twice — second call log shows FTS/vector/graph only, no inference escalation.

## Goal Link
none: factory-of-factories — generalizing Igor's capabilities to all agents in the system

## Alternatives considered
- Typed payload wholesale redesign of clan.memories (chose additive approach — payloads jsonb column preserves existing data, no migration risk)
- Building recall on top of existing research(X) tool (chose separate API — inference cost model is fundamentally different; conflating them would undermine the compiled inference principle)

## Constraints
- clan.memories MEDIUM inertia; memory/models.py HIGH inertia (models.py touch pre-approved by Akien 2026-05-28: "evolutionary improvement; schema did its job for hundreds of commits")
- interpretive_edges MEDIUM inertia
- Scraps embedding engine: new device, LOW inertia
- T-memory-agent-write-api superseded by T-memory-write-path

## Extends
D-shared-memory-service-2026-05-28 — this decision refines and extends the shared memory service architecture with a concrete retrieval API and typed graph design.
