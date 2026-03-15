#!/usr/bin/env python3
"""
cc_queue.py — Designer/Worker Claude task queue manager.

Queue file: ~/.TheIgors/cc_channel/queue.json
Log file:   ~/.TheIgors/cc_channel/log.jsonl

Usage:
    cc_queue.py list              — show all tasks (pending first)
    cc_queue.py add <json-file>   — add task from JSON file
    cc_queue.py claim <id>        — mark task in_progress
    cc_queue.py done <id> <msg>   — mark task completed with result
    cc_queue.py block <id> <msg>  — mark task blocked with reason
    cc_queue.py show <id>         — show full task detail
    cc_queue.py log <msg>         — append a free-form log entry
"""

import json
import os
import sys
from datetime import datetime, timezone

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


COMMANDS = {
    "list": cmd_list,
    "show": cmd_show,
    "claim": cmd_claim,
    "done": cmd_done,
    "block": cmd_block,
    "log": cmd_log,
    "add": cmd_add,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
