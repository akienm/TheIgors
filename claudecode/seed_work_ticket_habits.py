"""
seed_work_ticket_habits.py — D273 Igor self-coding review gate habits.

Updates PROC_CODE_A_TICKET to add the review gate (steps 8-10).
Seeds PROC_APPROVE_CHANGE — fires on approval → git commit → done.
Seeds PROC_CHECK_IGOR_QUEUE — lets Igor discover worker=igor tickets.

Run once after deploying:
  IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 \
    python3 claudecode/seed_work_ticket_habits.py

Safe to re-run — upserts on conflict.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault(
    "IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "Igor-wild-0001" / "wild-0001.db"),
)
DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
os.environ["IGOR_HOME_DB_URL"] = DB_URL


def seed_pg(habit: dict) -> None:
    import psycopg2

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute(
        """
        INSERT INTO memories
            (id, narrative, memory_type, source, confidence,
             context_of_encoding, timestamp, updated_at,
             metadata, portable, scope)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'class')
        ON CONFLICT (id) DO UPDATE SET
            narrative  = EXCLUDED.narrative,
            metadata   = EXCLUDED.metadata,
            updated_at = EXCLUDED.updated_at
        """,
        (
            habit["id"],
            habit["narrative"],
            habit["memory_type"],
            habit.get("source", "seed"),
            habit.get("confidence", 1.0),
            habit.get("context_of_encoding", "seed_work_ticket_habits D273"),
            now,
            now,
            json.dumps(habit["metadata"]),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"  [upserted] {habit['id']}")


# ── 1. PROC_CODE_A_TICKET — extend with review gate ──────────────────────────

seed_pg(
    {
        "id": "PROC_CODE_A_TICKET",
        "narrative": (
            "When I have a coding ticket to work (worker=igor), I follow this loop. "
            "I am the worker. No one is coming to help. I do each step myself.\n\n"
            "0. CLAIM AND ANNOUNCE. Run:\n"
            "   python3 ~/TheIgors/claudecode/cc_queue.py claim <ticket-id>\n"
            "   python3 ~/TheIgors/claudecode/channel.py post 'T-<id>: claimed. Starting.' --as igor\n\n"
            "1. READ THE TICKET. Run: python3 ~/TheIgors/claudecode/cc_queue.py show <id>\n"
            "   Post to channel: 'T-<id>: ticket read. Description: <one line>.'\n\n"
            "2. GREP THE CODEBASE. Find the relevant files before deciding what "
            "to change. Use run_bash with grep/glob to locate the function, class, or "
            "pattern. Never assume I know where something lives.\n"
            "   Post to channel: 'T-<id>: found files: <list>.'\n\n"
            "3. READ THE FILES. Read every file I plan to touch before editing. "
            "Understand what's already there. No blind edits.\n"
            "   Post to channel: 'T-<id>: read <files>. Plan: <one sentence>.'\n\n"
            "4. PLAN IN ONE PARAGRAPH. State: which files change, what the fix "
            "does, what test verifies it, what is NOT changing. Keep it tight.\n"
            "   Post to channel: 'T-<id>: plan: <paragraph>.'\n\n"
            "5. SELF_EDIT. Make the changes using patch_source_file. One targeted "
            "edit at a time. If the edit is larger than expected, stop and re-plan.\n"
            "   Post to channel: 'T-<id>: edit done — <what changed in one line>.'\n\n"
            "6. RUN PYTEST. Use run_bash: cd ~/TheIgors && source venv/bin/activate && "
            "python -m pytest tests/ -x -q. Tests must be green before proceeding. "
            "If tests fail, diagnose and fix — do not skip.\n"
            "   Post to channel: 'T-<id>: tests pass.' or 'T-<id>: tests FAIL — <error>.'\n\n"
            "7. DEPOSIT EPISODIC. Record what was done: what changed, what the "
            "test showed, what I learned.\n\n"
            "8. POST DIFF SUMMARY. Use run_bash: git diff HEAD --stat\n"
            "   Post to channel: 'T-<id>: changed <files>. Tests pass. Awaiting review.'\n\n"
            "9. MARK NEEDS_REVIEW. Run:\n"
            "   python3 ~/TheIgors/claudecode/cc_queue.py needs-review <ticket-id>\n\n"
            "10. WAIT. Do not commit. Do not restart. Akien reviews the diff and "
            "says 'approved' or 'looks good' to proceed. If changes are needed, "
            "Akien will say what to fix — go back to step 5.\n\n"
            "HARD RULE: Igor never self-initiates a git commit or restart. "
            "Those are human checkpoints.\n\n"
            "REMINDER: Use run_bash (not bash) for all shell commands."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "D273 review gate + channel visibility — seed_work_ticket_habits 2026-03-31b",
        "metadata": {
            "habit_type": "cognitive",
            "trigger": (
                "implement ticket|work the ticket|code a ticket|fix the ticket"
                "|work ticket|igor implement|worker=igor|patch source"
                "|sprint|self_edit|run pytest|what ticket|next ticket"
                "|canonical exercise|cloud escape"
            ),
            "why": (
                "Lever 3 of the igor-codes-himself roadmap, with D273 review gate. "
                "Steps 8-10 prevent Igor from self-committing and self-restarting "
                "before Akien has reviewed the diff. This is the safety layer while "
                "Igor builds a track record."
            ),
            "inertia": 0.35,
        },
    }
)

# ── 2. PROC_APPROVE_CHANGE — approval → commit → done ────────────────────────

seed_pg(
    {
        "id": "PROC_APPROVE_CHANGE",
        "narrative": (
            "When Akien approves a change I've implemented and marked needs_review, "
            "I run the commit cycle:\n\n"
            "1. IDENTIFY THE TICKET. Akien will say 'approved T-xxx' or 'looks good' "
            "(implying the most recent needs_review ticket). Find the ticket ID.\n\n"
            "2. CHECK CHANGED FILES. Run: git diff HEAD --name-only to see what's staged. "
            "If nothing is staged, run: git status to identify modified files.\n\n"
            "3. STAGE FILES. Run: git add <specific-files>. Never git add -A.\n\n"
            "4. COMMIT. Use format:\n"
            "   git commit -m 'fix/feat: <one-line description> — closes <ticket-id>\\n\\n"
            "   Co-Authored-By: Igor <igor@theigors.local>'\n\n"
            "5. MARK DONE. Run: "
            "python3 ~/TheIgors/claudecode/cc_queue.py done <ticket-id> '<what was built>'\n\n"
            "6. POST TO CHANNEL. Say: 'T-<id> committed. <one-line summary>'\n\n"
            "7. IF RESTART NEEDED. Say: 'Restart needed to pick up <what changed>. "
            "Say restart igor when ready.' Never write the restart flag myself.\n\n"
            "HARD RULE: I only run this habit when Akien explicitly says 'approved', "
            "'looks good', 'commit that', 'ship it', or similar approval phrase. "
            "I never commit on my own initiative."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "D273 review gate — seed_work_ticket_habits 2026-03-31",
        "metadata": {
            "habit_type": "cognitive",
            "trigger": (
                "approved|looks good|commit that|ship it|approve the change"
                "|approve that|lgtm|that looks good|go ahead and commit"
            ),
            "applies_when": (
                "A ticket is in needs_review state and Akien has given explicit approval"
            ),
            "why": (
                "D273: Igor never self-commits. The approval phrase is the human "
                "checkpoint. This habit fires only on explicit approval, never speculatively."
            ),
            "inertia": 0.40,
        },
    }
)

# ── 3. PROC_CHECK_IGOR_QUEUE — discover worker=igor tickets ──────────────────

seed_pg(
    {
        "id": "PROC_CHECK_IGOR_QUEUE",
        "narrative": (
            "When I want to find work assigned to me, or when Akien says "
            "'check your queue' / 'what tickets do you have' / 'any work for you', "
            "I run:\n\n"
            "  python3 ~/TheIgors/claudecode/cc_queue.py list\n\n"
            "Then filter for lines containing '[igor]' — these are tickets with "
            "worker=igor. I report the pending ones to channel:\n\n"
            "'My queue: T-xxx (S) <title>, T-yyy (M) <title>. "
            'Say "work ticket T-xxx" to start.\'\n\n'
            "If the queue has a needs_review ticket, I mention it first: "
            "'T-xxx is awaiting your review.'\n\n"
            "I do not auto-claim tickets. I report and wait for direction."
        ),
        "memory_type": "PROCEDURAL",
        "source": "seed",
        "confidence": 1.0,
        "context_of_encoding": "D273 — seed_work_ticket_habits 2026-03-31",
        "metadata": {
            "habit_type": "cognitive",
            "trigger": (
                "check your queue|what tickets do you have|any work for you"
                "|what should i work on|igor queue|my tickets|work assigned"
                "|check queue|pending tickets for igor"
            ),
            "why": (
                "D273: Igor needs to be able to discover his own work assignments "
                "without being hand-fed a ticket ID. This habit surfaces the "
                "worker=igor queue and waits for explicit direction."
            ),
            "inertia": 0.30,
        },
    }
)

print("\nDone. Verify with:")
print("  mcp__igor__memory_get PROC_CODE_A_TICKET")
print("  mcp__igor__memory_get PROC_APPROVE_CHANGE")
print("  mcp__igor__memory_get PROC_CHECK_IGOR_QUEUE")
