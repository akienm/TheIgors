# Do not — explicit destructive-action blocklist

**Path:** `theigors/rules/do-not`
**Updated:** 2026-04-21 by T-palace-rules-versioned

Destructive-action blocklist (never do these without explicit Akien go-ahead):
- Move or rename brainstem/ contents without Akien review.
- Delete ~/.TheIgors/Igor-wild-0001/wild-0001.db — that's the live DB.
- Edit .env without noting what changed and why.
- `git commit --amend`. Always new commits.
- `git push --force` to main.
- Enable IGOR_TIER5_ENABLED or IGOR_ARBITER_ENABLED.
- Skip pre-commit hooks with --no-verify.
- Write to decisions_log.dsb directly (it's generated now).

These live here because the cost of forgetting is high and irreversible. Keep this list short and absolute; everything else goes in context-specific rule nodes.

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)

