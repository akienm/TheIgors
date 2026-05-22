# D-deferred-inference-2026-05-21
**title:** Add deferred-resolution node state to Igor's inference engine
**date:** 2026-05-21
**status:** open
**spawned_tickets:** T-igor-deferred-node-state

## Decision narrative
Igor currently resolves nodes at query time — if evidence is insufficient it either
assigns a low-confidence answer or drops the node. This is lossy. The correct behavior
(modeled on how humans learn words from context) is to hold the node in an explicit
"clear/unresolved" state, flag it as a watchlist item, and let subsequent passes
accumulate edges. Resolution happens naturally when enough edges attach; if surrounding
context renders the node irrelevant, it stays clear but stops being watched.

Forcing early resolution is lossy because it substitutes a dictionary-style definition
for the richer network of contextual edges that give a concept its actual color.

## Hypothesis
Igor nodes with insufficient evidence should remain explicitly unresolved rather than
receiving low-confidence guesses, and should accumulate edges from subsequent context
passes until a resolution threshold is crossed naturally.

## Measurement Signal
A node queried with thin context returns status "unresolved" (not a low-confidence
answer). A second query with richer context either resolves it or keeps it flagged.
Verifiable by inspecting node state before and after additional context passes.

## Goal Link
none: this is a cognitive architecture quality improvement, not tied to a specific
G-xxx product goal — but it underpins the accuracy of all inference Igor performs.
