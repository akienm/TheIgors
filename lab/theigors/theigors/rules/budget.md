# Budget — present numbers, decide explicitly

**Path:** `theigors/rules/budget`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Present the numbers; Akien decides the spending tier. CC is flat-rate Pro Max, so the meter to minimize is Igor's OR spend.

Before flipping a feature gate: verify end-to-end that the output path produces real user-facing text, not stubs. This is the recurring failure mode — a feature reads 'enabled' without the downstream path carrying the signal to a user.

revision: 2026-04-21 — reframed to approach-target (T-audit-cc-rules-approach-frame)

