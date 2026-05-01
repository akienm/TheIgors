# Recency trumps age — newer descriptions hold more validity in almost all cases

**Path:** `theigors/rules/recency-trumps-age`
**Updated:** 2026-05-01 by claude-haiku-4.5

Always trust the newer description over the older one within the same artifact tier. The project evolves; later framings have absorbed the lessons of earlier ones. When two descriptions of the same concept conflict, the newer one is the working truth unless the newer one is itself stale (overridden by something even newer, or contradicted by current code).

Composes with `theigors/rules/safeguards` and the conflict-resolution hierarchy (code > palace > CLAUDE.md > MEMORY.md):
- The hierarchy answers WHERE to look (which artifact wins).
- This rule answers WHEN to trust within an artifact (newer wins).

Apply: when ticket descriptions, decisions, design docs, palace rules, or comments conflict, default to the most-recent statement on the topic. Use git timestamps + dated revision markers + ticket update timestamps as the recency signal. The older statement is preserved in history but loses authority for present decisions.

Practical examples:
- A ticket carries multiple "refinement #N" sections — the latest refinement is the working baseline. Earlier refinements are context for how the thinking evolved, not parallel decisions.
- A subsystem docstring written six months ago vs. one written last week — last week wins; older docstring is debris if it now misleads.
- An older decision doc and a newer one on the same topic — newer is the operative call.

When the newer version is wrong, the response is: write a still-newer correction, not revive the older one. The chain only moves forward.

revision: 2026-05-01 — filed during cognition-delay design conversation, when Akien explicitly named the principle
