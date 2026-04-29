# Safeguards — target clean reversibility, check before high-blast-radius ops

**Path:** `theigors/rules/safeguards`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Always target clean reversibility. Taking high-impact actions only with explicit Akien go-ahead keeps the system recoverable from misunderstandings, typos, and drift.

Pre-action register — each operation's authoritative home carries the full rule shape; this node is the single place to skim before acting:

- brainstem/ moves or renames → always Akien-review at plan stage (`theigors/rules/coding`, HIGH-inertia).
- Live DB delete/reset — `~/.TheIgors/Igor-wild-0001/wild-0001.db` → always get explicit Akien approval (`theigors/rules/database`).
- .env edits → always stage by name and note what changed and why in the commit message (`theigors/rules/commits`).
- git history modifiers (`--amend`, `--force` push to main, `--no-verify` hook bypass) → always keep history append-only (`theigors/rules/commits`).
- Safety-gate flips (`IGOR_TIER5_ENABLED`, `IGOR_ARBITER_ENABLED`) → always leave off until prerequisite infrastructure (`theigors/rules/igor-constraints`).
- decisions_log.dsb direct writes → always use tickets or slate instead (`theigors/rules/memory`).

Before any of these: always confirm authorization exists in durable context (current session conversation, CLAUDE.md, or pre-approval via /review HIGH-inertia check). When not, always ask first.

revision: 2026-04-24 — binding-imperative pass (T-directed-positive-prompts-pass-1)
