---
name: day-close
description: End-of-day ritual — savestateauto, close slate, audit, update docs, commit.
model: haiku
model_exception: /day-close-audit step escalates to Sonnet for simplification review
---

# /day-close — Close out the day

## Steps

### 1. /savestateauto
Flush all in-flight state first.

### 2. Close today's slate
Update `~/.TheIgors/claudecode/YYYYMMDD.slate.txt`:
- Final status for each ticket: new, unchanged, done, closed, deferred
- Note the slate is closed

### 3. Day-close audit (MANDATORY)
Run `/day-close-audit` — all steps. This is not optional. (Renamed from `/audit` on 2026-04-20 to make role clearer: `/day-close-audit` is the debris-and-hygiene check; `/review` is the skill for reviewing plans and code.)
Log to: `~/.TheIgors/claudecode/logs/$(date +%Y%m%d).code_maintenance_reviews.log`

### 4. Fix small day-close-audit findings + commit
Small fixes (typo, missing log, dead import): fix now.
Bigger issues: /ticket them.
If code changed: `/commit`

### 5. Read today's session
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py show 1
```

### 6. Push tickets to GitHub
```bash
python3 ~/TheIgors/lab/claudecode/github_sync.py push-queue
```

### 7. Sync docs DB + render sessions
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/docs_sync.py sync
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py render
```

### 8. Update affected DSBs
For each subsystem touched today: update `updated=` date in header.
Run docs_sync after edits.

### 9. Create GitHub Discussion
```bash
gh api graphql -f query='mutation {
  createDiscussion(input: {
    repositoryId: "R_kgDORR89gw",
    categoryId: "DIC_kwDORR89g84C3wqk",
    title: "Day YYYY-MM-DD — <theme>",
    body: "## Done\n- ...\n\n## Tickets\n- ...\n\n## Next\n- ..."
  }) { discussion { number url } }
}'
```

### 10. Post slate to Discussion
Post today's closed slate as a comment on the day's Discussion.

### 11. Commit docs
```bash
git add lab/design_docs/ lab/design_docs_for_igor/ lab/docs/ lab/notes.log
git commit -m "docs: day-close YYYY-MM-DD — <theme>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git pull --rebase origin main && git push origin main
```

### 12. /savestateauto (final)

### 13. /savestate

## Hard rules
- Never skip audit (step 3)
- Never commit source code here — docs only
- Skip steps with nothing to update
