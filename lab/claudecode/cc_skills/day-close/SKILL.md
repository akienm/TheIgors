---
name: day-close
description: End-of-day ritual — savestateauto, close slate, audit, update docs, commit.
model: haiku
model_exception: /day-close-audit step escalates to Sonnet for simplification review
---

# /day-close — Close out the day

## Steps

### 1. Ensure today's slate exists
day-close typically runs at the start of the next day (after midnight rollover).
Every day has a slate — if the date has ticked over and the current-day slate
doesn't exist yet, create it now before closing the day being ended.

```bash
TODAY_SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
if [ ! -f "$TODAY_SLATE" ]; then
  cat > "$TODAY_SLATE" <<EOF
# Slate $(date +%Y-%m-%d)

## Planned

## Ad hoc

## Done today
EOF
fi
```

### 2. /savestateauto
Flush all in-flight state first.

### 3. Close the slate for the day being ended
Update `~/.TheIgors/claudecode/<closing-day>.slate.txt` (typically yesterday's
file when day-close runs after midnight):
- Final status for each ticket: new, unchanged, done, closed, deferred
- Note the slate is closed

### 4. Day-close audit (MANDATORY)
Run `/day-close-audit` — all steps. This is not optional. (Renamed from `/audit` on 2026-04-20 to make role clearer: `/day-close-audit` is the debris-and-hygiene check; `/review` is the skill for reviewing plans and code.)
Log to: `~/.TheIgors/claudecode/logs/$(date +%Y%m%d).code_maintenance_reviews.log`

### 5. Fix small day-close-audit findings + commit
Small fixes (typo, missing log, dead import): fix now.
Bigger issues: /ticket them.
If code changed: `/commit`

### 6. Read the closing slate
```bash
cat ~/.TheIgors/claudecode/<closing-day>.slate.txt
```

### 7. Push tickets to GitHub
```bash
python3 ~/TheIgors/lab/claudecode/github_sync.py push-queue
```

### 8. Sync docs DB
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/docs_sync.py sync
```

### 9. Update affected DSBs
For each subsystem touched today: update `updated=` date in header.
Run docs_sync after edits.

### 10. Create GitHub Discussion
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

### 11. Post slate to Discussion
Post the closed slate as a comment on the day's Discussion.

### 12. Commit docs
```bash
git add lab/design_docs/ lab/design_docs_for_igor/ lab/docs/ lab/notes.log
git commit -m "docs: day-close YYYY-MM-DD — <theme>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git pull --rebase origin main && git push origin main
```

### 13. /savestateauto (final)

### 14. /savestate

## Hard rules
- Every day has a slate — Step 1 guarantees the current-day slate exists even if day-close runs before context-load on the new day.
- Audit (step 4) runs every day-close — it's the hygiene gate.
- Commits during day-close are docs-only; source changes belong in /sprint commits.
- Skip steps with nothing to update.
