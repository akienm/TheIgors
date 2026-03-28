---
name: day-close
description: End-of-day docs + commit ritual for TheIgors project. Fixes test deficits, runs probes, automated audit, docs sync, gap analysis review, commit. Use when Akien says /day-close, "end of day", "wrap up docs", or "close out the day".
---

# Day-Close — End-of-Day Docs Ritual

Runs once at end of day (or end of a significant work block).
Session state is already in DB — this adds tests, behavior checks, docs sync, and gap review.
All steps are mechanical except Step 5 (gap analysis) which needs judgment.

---

## Step 1 — Fix test deficits

Check for test-debt items on the slate:
```bash
cat ~/.TheIgors/cc_channel/slate.md | grep -i "test-debt\|test debt\|missing test"
```

For each test-debt item: write the test now or confirm it's deferred to next slate.
Run tests to confirm baseline is green:
```bash
cd ~/TheIgors && source venv/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -20
```

If tests fail: run `/test-fix` before proceeding.

---

## Step 2 — Run defined probe tests

Check if any probe criteria are defined for today's work:
```bash
grep -r "probe:" ~/.TheIgors/cc_channel/slate.md 2>/dev/null || echo "no probes defined"
```

For each defined probe: run `/probe <criterion>`.
If no probes defined: skip this step.

---

## Step 3 — Automated audit ⛔ MANDATORY — NEVER SKIP

```
/audit
```

⛔ **This is not optional. Skipping the audit makes day-close incomplete.**
Runs all 17 steps. Note all findings.

---

## Step 4 — Fix small audit findings + commit fixes

For each finding from Step 3:
- **Small/obvious fix** (typo, missing log line, off-by-one): fix now
- **Bigger issue**: add to slate as a ticket, do not fix now

If any code was changed: commit before proceeding to docs.
```
/commit
```

---

## Step 5 — Read today's session record

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py show 1
```

Skim it — you need to know which DSBs to update in Step 7.

---

## Step 6 — Sync docs DB + render sessions.md

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001

# Sync all DSB files to Postgres
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/docs_sync.py sync

# Render sessions.md from DB
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py render
```

---

## Step 7 — Update affected subsystem DSBs

For each subsystem touched today (infer from session key_changes):
- Update `updated=` date in the DSB header
- Update only the specific lines that changed — do not rewrite

Common subsystems and their DSBs:
- `subsystem_memory.dsb` — cortex, db_proxy, models changes
- `subsystem_cognition.dsb` — thalamus, BG, NE, milieu changes
- `subsystem_inference.dsb` — reasoners, tier routing changes
- `subsystem_tools.dsb` — tool additions or changes
- `subsystem_reading.dsb` — ebook_reader, watcher changes
- `subsystem_self_edit.dsb` — self_edit, hot_reload changes
- `subsystem_web_network.dsb` — server.py, cc_bridge, channel changes

For tooling-only sessions (claudecode/ changes only): skip subsystem DSBs.
Run docs_sync after any DSB edits:
```bash
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/docs_sync.py sync
```

---

## Step 8 — Gap analysis review (judgment required)

Read the current gap_analysis:
```bash
head -60 ~/TheIgors/design_docs/gap_analysis.md
```

For each gap **closed** today:
- Add root cause + fix to `design_docs/gap_analysis.md`
- Mirror to `design_docs_for_igor/gap_analysis.dsb`: change status to `closed`

For each **new gap** surfaced today:
- Add to `design_docs/gap_analysis.md` as open item
- Add to `design_docs_for_igor/gap_analysis.dsb`: new `G-xxx|status|description` line

If no gaps opened or closed: skip this step.

---

## Step 9 — Update MEMORY.md if persistent facts changed

Read `~/.claude/projects/-home-akien-TheIgors/memory/MEMORY.md`.
Update only if something **non-obvious and durable** changed — architecture, known issues, priority shifts.
Do not add ephemeral notes. Do not duplicate what's already in sessions.md.

---

## Step 10 — Post GitHub discussion #62

Compose a brief session summary (3-5 bullets) and post:
```bash
gh api graphql -f query='mutation {
  addDiscussionComment(input: {
    discussionId: "D_kwDORR89g84AkjSM",
    body: "## Session YYYY-MM-DDx — <theme>\n\n**Decisions**: D130, D131\n**Done**: ...\n**Next**: ..."
  }) { comment { id } }
}'
```

Keep it short — it's a log entry, not an essay.

---

## Step 11 — Commit docs

Stage only docs/memory/design files:
```bash
git add design_docs/ design_docs_for_igor/ memory/ claudecode/
git diff --staged --stat
```

Confirm no source code, no .env, no runtime data in the diff. Then commit:
```bash
git commit -m "$(cat <<'EOF'
docs: day-close session YYYY-MM-DDx — <one-line theme>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
git pull --rebase origin main
git push origin main
```

If pull fails due to unstaged changes: `git stash && git pull --rebase origin main && git stash pop && git push origin main`

---

## Step 12 — Savestate

```
/savestate
```

---

## Hard rules

- Never commit source code here — docs only
- Never rewrite DSB files from scratch — update in place
- Never add speculative gaps — only things that actually happened
- Skip steps that have nothing to update — don't add noise
