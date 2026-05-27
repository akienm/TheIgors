# D-concept-layer-and-tags-2026-05-26
**title:** palace.concepts.* layer as peer to goals; tags as connective tissue
**date:** 2026-05-26
**status:** open
**spawned_tickets:** T-concept-skill, T-concept-palace-seed, T-sorted-concept-links, T-tag-vocabulary-connective-tissue, T-consequence-concept-layer-and-tags

## Decision narrative
Add a `palace.concepts.*` layer as a peer to `palace.goals.*` — both are foundational reference material at the same tier. Goals say where we're going; concepts say how things work. Decisions draw on both. The four-tier structure is: Goals + Concepts (same tier) → Decisions → Tickets. A `/concept` skill handles collaborative authoring: talk it over, accord check, write. Tags replace explicit cross-links across the whole stack — palace nodes and file headers share a tag vocabulary; related things are discovered by querying tags, not by maintaining links that break when things move.

## Hypothesis
A CC session reads a palace.concepts.* node cold and gets an architectural concept right without Akien correcting it.

## Measurement Signal
Zero re-explanations of a concept that has a palace.concepts.* node within 30 days of seeding. Observable: check whether subsequent design sessions contradict or re-explain any concept already in the palace.

## Goal Link
G-system-self-improving — better concept documentation is how the CC/Librarian/Igor stack learns from its own operation and stops needing the same re-explanations.

## Alternatives considered
- Explicit bidirectional links instead of tags — rejected: maintenance burden; links break when things move; tags degrade gracefully
- Concepts as a sequential layer between goals and decisions — rejected: concepts are reference material, not a stage; decisions draw on goals AND concepts as peers
