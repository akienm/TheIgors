# New Python files include an author-model tag

**Path:** `theigors/rules/author-model-tag`
**Updated:** 2026-04-29T19:00:00Z by cc

Every new Python file under wild_igor/, lab/utility_closet/, or lab/claudecode/ should include a tag near the top identifying the author model:

    # author-model: opus
    # author-model: sonnet
    # author-model: haiku
    # author-model: human
    # author-model: igor

The tag may live as a top-of-file comment OR inside the module docstring; case-insensitive.

Why: git blame surfaces who edited each line — but loses the original author once a file gets fully rewritten. The header tag preserves original-author provenance. Companion to T-blame-with-model (blame enrichment for already-committed lines).

Recognized tokens: opus, sonnet, haiku, human, igor, akien.

Exempt:
- tests/ files
- __init__.py
- Any file outside the enforced directories

Enforcement:
- audit_check_author_model_tag.py — scans new files in a diff range
- Default range: HEAD~1..HEAD (catches new files in the last commit)
- Run --staged at pre-commit time to catch before landing
- Run --range A..B for a custom span

Apply forward only — no retroactive backfill on existing files.

Filed: T-author-model-header-on-new-files (2026-04-29)
