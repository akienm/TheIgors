# Memory.metadata.comment — human-readable annotations on memories

**Path:** `theigors/rules/memory-comment-convention`
**Updated:** 2026-04-29T18:30:00Z by cc

Use Memory.metadata.comment to leave human-readable annotations on memories: why this memory exists, gotchas, sources, who decided what. Memory.add_comment(text) is the writer-side helper — it appends (joined by ' | ') so multiple authors can annotate without overwriting.

When to write a comment:
- HIGH-inertia memories (CORE_PATTERN, CHARACTER_PROFILE, IDENTITY_ANCHOR) — non-obvious 'why' belongs here, not in narrative.
- Self-edited rules where the rationale would otherwise rot out.
- Any memory whose narrative is terse and risks being misread later.

When NOT to write a comment:
- Activation count, friction history, embedding text — those have their own fields.
- Decisions — use /decided + decision_id linkage, not a comment.

Reading: Memory.comment property returns the field (empty string if unset).
Companion ticket T-payload-comment-opcode adds NOOP_COMMENT for in-payload comments at the opcode layer.

Filed: T-memory-metadata-comment-convention (2026-04-29)
