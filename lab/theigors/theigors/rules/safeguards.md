# Safeguards — target clean reversibility, check before high-blast-radius ops

**Path:** `theigors/rules/safeguards`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Target: clean reversibility. Taking high-impact actions only with explicit Akien go-ahead keeps the system recoverable from misunderstandings, typos, and drift.

Pre-action register. Each operation's authoritative home carries the full rule shape; this node is the single place to skim before acting:

- brainstem/ moves or renames → `theigors/rules/coding` (HIGH-inertia, Akien review at plan stage).
- Live DB delete/reset — `~/.TheIgors/Igor-wild-0001/wild-0001.db` → `theigors/rules/database` (explicit Akien approval).
- .env edits → `theigors/rules/commits` (stage by name; note what changed and why in the commit message).
- git history modifiers (`--amend`, `--force` push to main, `--no-verify` hook bypass) → `theigors/rules/commits` (append-only history, integrity preserved).
- Safety-gate flips (`IGOR_TIER5_ENABLED`, `IGOR_ARBITER_ENABLED`) → `theigors/rules/igor-constraints` (both gated OFF until prerequisite infrastructure).
- decisions_log.dsb direct writes → `theigors/rules/memory` (generated file; use tickets or slate instead).

Before any of these: confirm authorization exists in durable context (current session conversation, CLAUDE.md, or pre-approval via /review HIGH-inertia check). If not, ask.

revision: 2026-04-21 — reframed from 'do-not' proscriptive-list to approach-target cross-index (T-audit-cc-rules-approach-frame).

