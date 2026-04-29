# Commits — full cycle, new commits, integrity preserved

**Path:** `theigors/rules/commits`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Always treat each commit as an atomic full cycle: stage specific files, commit, `pull --rebase`, push. Always create a new commit — stash when pull needs a clean tree.

Autonomous commit rights: when tests pass and no secrets are in the diff, always commit without asking — that's the pre-approved shape.

Always stage files explicitly by name. Name-staging keeps `.env`, `*.db`, and runtime paths under `~/.TheIgors/` out of commits automatically.

Always preserve git history integrity:
- Always let pre-commit hooks run (never use `--no-verify`).
- Always push non-force to main (never `--force` on main).
- Always create new commits (never `git commit --amend`, even when the amend "seems harmless").
- Always stash before `pull --rebase` when the working tree is dirty.

revision: 2026-04-24 — binding-imperative pass (T-directed-positive-prompts-pass-1)
