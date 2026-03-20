#!/usr/bin/env python3
"""
cc_queue.py — Designer/Worker Claude task queue manager.

Queue file: ~/.TheIgors/cc_channel/queue.json
Log file:   ~/.TheIgors/cc_channel/log.jsonl

Usage:
    cc_queue.py list                          — show all tasks (pending first)
    cc_queue.py add <json-file>               — add task from JSON file
    cc_queue.py claim <id>                    — mark task in_progress
    cc_queue.py done <id> <msg>               — mark task completed with result
    cc_queue.py block <id> <msg>              — mark task blocked with reason
    cc_queue.py show <id>                     — show full task detail
    cc_queue.py log <msg>                     — append a free-form log entry
    cc_queue.py flush_decision <id> <summary> — flush decision to Igor memory
    cc_queue.py flush_session <session> <summary> — flush session blob to Igor memory
    cc_queue.py worker-launch <ticket-id>         — launch a worker konsole and record its PID
    cc_queue.py inject <ticket-id> <text>         — send keystrokes to worker terminal via xdotool
"""

import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

IGOR_NOTEBOOK_URL = "https://localhost:8080/api/cc_notebook"


def _ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


QUEUE_PATH = os.path.expanduser("~/.TheIgors/cc_channel/queue.json")
LOG_PATH = os.path.expanduser("~/.TheIgors/cc_channel/log.jsonl")
STATUS_ORDER = {"pending": 0, "in_progress": 1, "blocked": 2, "done": 3}


def _load():
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH) as f:
        return json.load(f)


def _save(tasks):
    os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
    with open(QUEUE_PATH, "w") as f:
        json.dump(tasks, f, indent=2)


def _log(entry: dict):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _find(tasks, tid):
    for t in tasks:
        if t["id"] == tid:
            return t
    return None


def cmd_list(args):
    tasks = _load()
    if not tasks:
        print("Queue empty.")
        return
    tasks_sorted = sorted(
        tasks, key=lambda t: (STATUS_ORDER.get(t["status"], 9), t.get("priority", 99))
    )
    STATUS_ICON = {"pending": "⬜", "in_progress": "🔵", "blocked": "🔴", "done": "✅"}
    for t in tasks_sorted:
        icon = STATUS_ICON.get(t["status"], "?")
        size = t.get("size", "?")
        print(f"  {icon} [{t['id']}] ({size}) {t['title']}  [{t['status']}]")
        if t["status"] == "blocked" and t.get("result"):
            print(f"       BLOCKED: {t['result']}")
        if t["status"] == "done" and t.get("result"):
            print(f"       done: {t['result']}")


def cmd_show(args):
    if not args:
        print("Usage: show <id>")
        sys.exit(1)
    tasks = _load()
    t = _find(tasks, args[0])
    if not t:
        print(f"Task {args[0]} not found.")
        sys.exit(1)
    print(json.dumps(t, indent=2))


def cmd_claim(args):
    if not args:
        print("Usage: claim <id>")
        sys.exit(1)
    tasks = _load()
    t = _find(tasks, args[0])
    if not t:
        print(f"Task {args[0]} not found.")
        sys.exit(1)
    if t["status"] != "pending":
        print(f"Task {args[0]} is {t['status']}, not pending.")
        sys.exit(1)
    t["status"] = "in_progress"
    t["claimed_at"] = _now()
    _save(tasks)
    _log({"action": "claim", "id": args[0], "title": t["title"]})
    print(f"Claimed {args[0]}: {t['title']}")


def cmd_done(args):
    if len(args) < 2:
        print("Usage: done <id> <result-message>")
        sys.exit(1)
    tasks = _load()
    t = _find(tasks, args[0])
    if not t:
        print(f"Task {args[0]} not found.")
        sys.exit(1)
    t["status"] = "done"
    t["result"] = args[1]
    t["completed_at"] = _now()
    _save(tasks)
    _log({"action": "done", "id": args[0], "title": t["title"], "result": args[1]})
    print(f"Completed {args[0]}: {t['title']}")


def cmd_block(args):
    if len(args) < 2:
        print("Usage: block <id> <reason>")
        sys.exit(1)
    tasks = _load()
    t = _find(tasks, args[0])
    if not t:
        print(f"Task {args[0]} not found.")
        sys.exit(1)
    t["status"] = "blocked"
    t["result"] = args[1]
    t["blocked_at"] = _now()
    _save(tasks)
    _log({"action": "blocked", "id": args[0], "title": t["title"], "reason": args[1]})
    print(f"Blocked {args[0]}: {args[1]}")


def cmd_log(args):
    if not args:
        print("Usage: log <message>")
        sys.exit(1)
    msg = " ".join(args)
    _log({"action": "note", "message": msg})
    print(f"Logged: {msg}")


def cmd_add(args):
    """Add tasks from a JSON file (array of task objects) or inline JSON string."""
    if not args:
        print("Usage: add <json-file-or-inline-json>")
        sys.exit(1)
    src = args[0]
    if os.path.exists(src):
        with open(src) as f:
            new_tasks = json.load(f)
    else:
        new_tasks = json.loads(src)
    if isinstance(new_tasks, dict):
        new_tasks = [new_tasks]
    tasks = _load()
    existing_ids = {t["id"] for t in tasks}
    added = 0
    for nt in new_tasks:
        if nt["id"] in existing_ids:
            print(f"  skip (exists): {nt['id']}")
            continue
        nt.setdefault("status", "pending")
        nt.setdefault("result", None)
        nt.setdefault("claimed_at", None)
        nt.setdefault("completed_at", None)
        tasks.append(nt)
        _log({"action": "add", "id": nt["id"], "title": nt["title"]})
        print(f"  added: {nt['id']} — {nt['title']}")
        added += 1
    _save(tasks)
    print(f"Added {added} task(s).")


def _igor_post(payload: dict) -> bool:
    """POST JSON to Igor's cc_notebook endpoint. Returns True on success."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        IGOR_NOTEBOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5, context=_ssl_ctx()):
            return True
    except Exception as e:
        _log(
            {
                "action": "flush_failed",
                "error": str(e),
                "payload_key": payload.get("key"),
            }
        )
        print(f"  [Igor flush failed — Igor not running? {e}]")
        return False


def cmd_flush_decision(args):
    """Flush a design decision to Igor's cc_notebook memory."""
    if len(args) < 2:
        print("Usage: flush_decision <id> <summary>")
        sys.exit(1)
    decision_id = args[0]
    summary = " ".join(args[1:])
    session = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = {
        "employer_id": "claude",
        "key": decision_id,
        "content": json.dumps(
            {
                "type": "decision",
                "id": decision_id,
                "summary": summary,
                "session": session,
            }
        ),
    }
    if _igor_post(payload):
        _log({"action": "flush_decision", "id": decision_id, "summary": summary})
        print(f"Flushed {decision_id} to Igor: {summary[:80]}")
    else:
        print(f"  (decision logged locally only)")


def cmd_flush_session(args):
    """Flush a session summary blob to Igor's cc_notebook memory."""
    if len(args) < 2:
        print("Usage: flush_session <session_id> <summary>")
        sys.exit(1)
    session_id = args[0]
    summary = " ".join(args[1:])
    payload = {
        "employer_id": "claude",
        "key": f"session_{session_id}",
        "content": json.dumps(
            {
                "type": "session_summary",
                "session": session_id,
                "summary": summary,
                "ts": _now(),
            }
        ),
    }
    if _igor_post(payload):
        _log({"action": "flush_session", "session": session_id})
        print(f"Flushed session {session_id} to Igor")
    else:
        print(f"  (session logged locally only)")


WORKER_PIDS_PATH = os.path.expanduser("~/.TheIgors/cc_channel/worker_pids.json")


def _load_worker_pids():
    if not os.path.exists(WORKER_PIDS_PATH):
        return {}
    with open(WORKER_PIDS_PATH) as f:
        return json.load(f)


def _save_worker_pids(pids):
    os.makedirs(os.path.dirname(WORKER_PIDS_PATH), exist_ok=True)
    with open(WORKER_PIDS_PATH, "w") as f:
        json.dump(pids, f, indent=2)


def cmd_worker_launch(args):
    """Launch a worker konsole for a ticket and record its PID."""
    import subprocess

    if not args:
        print("Usage: worker-launch <ticket-id>")
        sys.exit(1)
    ticket_id = args[0]
    # Launch konsole with worker context
    proc = subprocess.Popen(
        [
            "konsole",
            "--separate",
            "-e",
            "bash",
            "-c",
            (
                f"source ~/TheIgors/venv/bin/activate && "
                f"export WORKER_TICKET={ticket_id} && "
                f"claude --dangerously-skip-permissions "
                f'"/sprint {ticket_id}"; exec bash'
            ),
        ],
        start_new_session=True,
    )
    pids = _load_worker_pids()
    pids[ticket_id] = {
        "konsole_pid": proc.pid,
        "launched_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_worker_pids(pids)
    print(f"Launched worker for {ticket_id} — konsole PID {proc.pid}")
    print(f"Recorded in {WORKER_PIDS_PATH}")


def cmd_inject(args):
    """Send keystrokes to a worker terminal via xdotool."""
    import subprocess

    if len(args) < 2:
        print("Usage: inject <ticket-id> <text>")
        sys.exit(1)
    ticket_id = args[0]
    text = " ".join(args[1:])
    pids = _load_worker_pids()
    entry = pids.get(ticket_id)
    if not entry:
        print(f"No worker PID recorded for {ticket_id}. Run worker-launch first.")
        sys.exit(1)
    konsole_pid = entry["konsole_pid"]
    # Find the window ID for this konsole process
    result = subprocess.run(
        ["xdotool", "search", "--pid", str(konsole_pid)], capture_output=True, text=True
    )
    wids = result.stdout.strip().splitlines()
    if not wids:
        print(
            f"No xdotool window found for konsole PID {konsole_pid}. Is it still running?"
        )
        sys.exit(1)
    wid = wids[-1]  # use last window (most recently created)
    subprocess.run(
        ["xdotool", "type", "--window", wid, "--clearmodifiers", text + "\n"]
    )
    print(f"Injected into {ticket_id} (window {wid}): {text!r}")


COMMANDS = {
    "list": cmd_list,
    "show": cmd_show,
    "claim": cmd_claim,
    "done": cmd_done,
    "block": cmd_block,
    "log": cmd_log,
    "add": cmd_add,
    "flush_decision": cmd_flush_decision,
    "flush_session": cmd_flush_session,
    "worker-launch": cmd_worker_launch,
    "inject": cmd_inject,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
