---
name: commit means full cycle
description: When Akien says "commit", do the full add/commit/pull/push cycle — not just git commit
type: feedback
---

When Akien says "commit", execute the full cycle:
1. `git add` relevant files (or -A if context is clear)
2. `git commit -m "..."`
3. `git pull` (rebase)
4. `git push` — only if pull had no errors

**Why:** Akien has a bash script `gitcommitandpush` that does this as one operation. He was trying to replicate the same discipline for Claude Code. Nothing ever gets out of sync this way.

**How to apply:** Any time Akien says "commit" or "commit this", treat it as the full cycle unless he explicitly says otherwise (e.g. "just commit, don't push yet").

**Caveat:** Still read the diff before staging. .gitignore protects sensitive files but confirm nothing unexpected is staged.
