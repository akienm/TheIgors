# Commits — full cycle, no amend, no force-push

**Path:** `theigors/rules/commits`
**Updated:** 2026-04-21 by T-palace-rules-versioned

Commit discipline:
- Commit = full cycle: add + commit + pull + push. Never partial.
- Autonomous commit rights: tests pass + no secrets = commit without asking.
- Never `--no-verify` or force-push main.
- Never stage .env, *.db, or ~/.TheIgors/ runtime paths.
- Never `git commit --amend`. Always new commits, even when the amend 'seems harmless.' Stash is the right tool when `pull --rebase` fails on unstaged changes.

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)

