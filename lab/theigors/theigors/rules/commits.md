# Commits — full cycle, new commits, integrity preserved

**Path:** `theigors/rules/commits`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Commits are atomic full cycles: stage specific files, commit, `pull --rebase`, push. Every change is a new commit — stash when pull needs a clean tree.

Autonomous commit rights: tests pass + no secrets = commit without asking.

Stage files explicitly by name. That keeps .env, *.db, and ~/.TheIgors/ runtime paths off the commit.

Preserve git history integrity: hooks run (no `--no-verify`), pushes don't force (no `--force` on main), history stays append-only (no `git commit --amend`, even when the amend 'seems harmless'). Stash is the right tool when `pull --rebase` fails on unstaged changes.

revision: 2026-04-21 — reframed to approach-target (T-audit-cc-rules-approach-frame)

