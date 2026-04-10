#!/usr/bin/env bash
# run_review_audit.sh — launch Worker Claude to run the codebase health audit
# Called by cron (2am daily while change rate high) or manually.
# Worker reads review_audit.md and runs through all 10 checks in one session.

set -euo pipefail

REPO="$HOME/TheIgors"
LOG="$HOME/.TheIgors/logs/review_audit.log"
TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')

mkdir -p "$(dirname "$LOG")"
echo "$TIMESTAMP  run_review_audit: starting" >> "$LOG"

# Check if change rate warrants a run
RECENT_COMMITS=$(git -C "$REPO" log --oneline --since='7 days ago' 2>/dev/null | wc -l)
echo "$TIMESTAMP  recent_commits_7d=$RECENT_COMMITS" >> "$LOG"

# Add audit task to Worker queue
TASK_MSG="Run codebase health audit per claudecode/review_audit.md. Work through all 10 checks. Post findings to GitHub discussion #62 as a comment. Format: [OK] or [CHECK] file:line — description per item."

python3 "$REPO/claudecode/cc_queue.py" add \
  --title "Codebase health audit $(date '+%Y-%m-%d')" \
  --body "$TASK_MSG" \
  --size S \
  2>> "$LOG"

echo "$TIMESTAMP  run_review_audit: task queued for Worker" >> "$LOG"
