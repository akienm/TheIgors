# Preferred paths — deprecated → preferred form pairs

**Path:** `theigors/rules/preferred_paths`
**Updated:** 2026-04-29 by cc-sprint

Declarative list of anti-patterns Sonnet falls back to, paired with the preferred alternative.
Each child node carries: applies_when, deprecated, preferred, why.
Read by audit-precode (before first edit) and audit-smell (post-write catch).
New entries via T-rule-preferred-paths-code-scan scan or Akien observation.
