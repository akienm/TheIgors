#!/usr/bin/env python3
"""
igor_admin.py — Unified CLI entry point for all cc-admin operations.

Delegates to api.py functions in-process (no subprocess).

Usage:
    igor-admin ticket list|add|claim|done|block
    igor-admin session start|append-change|finalize|show
    igor-admin decision add|get|show|resolve|open
    igor-admin channel post|read
    igor-admin env --check

Ref: T-cc-admin-consolidation
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure lab/claudecode is importable
_CC_DIR = Path(__file__).resolve().parent
if str(_CC_DIR) not in sys.path:
    sys.path.insert(0, str(_CC_DIR))

import api

# ── ticket subcommands ────────────────────────────────────────────────────────


def cmd_ticket(args):
    sub = args.subcmd
    if sub == "list":
        flags = []
        if args.gated:
            flags.append("--gated")
        if args.by_decision:
            flags.append("--by-decision")
        api.list_tickets(flags)
    elif sub == "add":
        api.add_ticket(args.source)
    elif sub == "claim":
        print(
            "ERROR: 'claim' subcommand is removed. "
            "Workers must request tickets via: cc_queue.py next --worker <name>",
            file=sys.stderr,
        )
        sys.exit(1)
    elif sub == "done":
        api.done_ticket(args.id, args.msg)
    elif sub == "block":
        api.block_ticket([args.id, args.msg])
    elif sub == "show":
        api.show_ticket([args.id])
    else:
        print(f"Unknown ticket subcommand: {sub}")
        sys.exit(2)


# ── session subcommands ───────────────────────────────────────────────────────


def cmd_session(args):
    sub = args.subcmd
    if sub == "start":
        api.start_session([args.id, args.theme])
    elif sub == "append-change":
        parts = []
        if args.id:
            parts.append(args.id)
        parts.append(args.change)
        api.append_change(parts)
    elif sub == "append-decision":
        parts = []
        if args.id:
            parts.append(args.id)
        parts.append(args.decision_id)
        api.append_decision(parts)
    elif sub == "finalize":
        parts = [args.id, args.next_session]
        if args.in_flight:
            parts.append(args.in_flight)
        api.finalize_session(parts)
    elif sub == "show":
        n = args.n if args.n else 5
        api.show_session(n)
    elif sub == "get":
        api.get_session(args.id)
    else:
        print(f"Unknown session subcommand: {sub}")
        sys.exit(2)


# ── decision subcommands ──────────────────────────────────────────────────────


def cmd_decision(args):
    sub = args.subcmd
    if sub == "add":
        api.add_decision([args.id, args.short_name, args.status, args.description])
    elif sub == "get":
        api.get_decision(args.id)
    elif sub == "show":
        n = args.n if args.n else 10
        api.show_decisions(n)
    elif sub == "resolve":
        notes = args.notes or ""
        api.resolve_decision(args.id, args.resolution, notes)
    elif sub == "open":
        api.open_decisions()
    else:
        print(f"Unknown decision subcommand: {sub}")
        sys.exit(2)


# ── channel subcommands ───────────────────────────────────────────────────────


def cmd_channel(args):
    sub = args.subcmd
    if sub == "post":
        entry = api.post_message(args.message, author=args.author or "")
        print(f"Posted: {api.format_channel_entry(entry)}")
    elif sub == "read":
        n = args.n if args.n else 20
        entries = api.read_messages(n)
        if not entries:
            print("(channel is empty)")
        for e in entries:
            print(api.format_channel_entry(e))
    else:
        print(f"Unknown channel subcommand: {sub}")
        sys.exit(2)


# ── env subcommand ────────────────────────────────────────────────────────────


def cmd_env(args):
    import re

    def _mask(url: str) -> str:
        # Mask password: postgresql://user:PASSWORD@host/db → postgresql://user:****@host/db
        return re.sub(r"(:)[^:@]+(@)", r"\1****\2", url)

    db_url = os.environ.get("IGOR_HOME_DB_URL", "")
    source_label = "IGOR_HOME_DB_URL"
    if not db_url:
        db_url = os.environ.get("IGOR_DB_URL", "")
        source_label = "IGOR_DB_URL (fallback)"

    if not db_url:
        print("IGOR_HOME_DB_URL is NOT set", file=sys.stderr)
        sys.exit(1)

    print(f"{source_label} is set: {_mask(db_url)}")

    # Trivial connectivity query — verifies Postgres is reachable & creds work.
    try:
        import psycopg2
    except ImportError as e:
        print(f"psycopg2 not importable: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        conn = psycopg2.connect(db_url, connect_timeout=3)
        try:
            with conn.cursor() as c:
                c.execute("SELECT 1")
                c.fetchone()
        finally:
            conn.close()
        print(f"Postgres reachable at {_mask(db_url)}")
    except Exception as e:
        print(
            f"Postgres UNREACHABLE at {_mask(db_url)}: {e}",
            file=sys.stderr,
        )
        sys.exit(3)


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser():
    p = argparse.ArgumentParser(
        prog="igor-admin",
        description="Unified CC admin CLI — delegates to api.py in-process.",
    )
    subs = p.add_subparsers(dest="command", required=True)

    # ── ticket ──
    tp = subs.add_parser("ticket", help="Ticket queue operations")
    tsub = tp.add_subparsers(dest="subcmd", required=True)

    tlist = tsub.add_parser("list", help="List tickets")
    tlist.add_argument("--gated", action="store_true", help="Include gated tickets")
    tlist.add_argument("--by-decision", action="store_true", dest="by_decision")

    tadd = tsub.add_parser("add", help="Add ticket(s) from JSON file or inline JSON")
    tadd.add_argument("source", help="JSON file path or inline JSON string")

    tdone = tsub.add_parser("done", help="Mark ticket done")
    tdone.add_argument("id", help="Ticket ID")
    tdone.add_argument("msg", help="Result message")

    tblock = tsub.add_parser("block", help="Mark ticket blocked")
    tblock.add_argument("id", help="Ticket ID")
    tblock.add_argument("msg", help="Block reason")

    tshow = tsub.add_parser("show", help="Show full ticket detail")
    tshow.add_argument("id", help="Ticket ID")

    # ── session ──
    sp = subs.add_parser("session", help="Session record operations")
    ssub = sp.add_subparsers(dest="subcmd", required=True)

    sstart = ssub.add_parser("start", help="Start a session")
    sstart.add_argument("id", help="Session ID (e.g. 2026-04-21a)")
    sstart.add_argument("theme", help="Session theme")

    sac = ssub.add_parser("append-change", help="Append a key-change line")
    sac.add_argument("change", help="Change description")
    sac.add_argument("--id", default=None, help="Session ID (default: current)")

    sad = ssub.add_parser("append-decision", help="Append a decision ID")
    sad.add_argument("decision_id", help="Decision ID (e.g. D133)")
    sad.add_argument("--id", default=None, help="Session ID (default: current)")

    sfin = ssub.add_parser("finalize", help="Finalize a session")
    sfin.add_argument("id", help="Session ID")
    sfin.add_argument("next_session", help="Next session plan")
    sfin.add_argument("--in-flight", dest="in_flight", default=None)

    sshow = ssub.add_parser("show", help="Show last N sessions")
    sshow.add_argument("n", nargs="?", type=int, default=5)

    sget = ssub.add_parser("get", help="Get one session by ID")
    sget.add_argument("id", help="Session ID")

    # ── decision ──
    dp = subs.add_parser("decision", help="Decision log operations")
    dsub = dp.add_subparsers(dest="subcmd", required=True)

    dadd = dsub.add_parser("add", help="Add a decision")
    dadd.add_argument("id", help="Decision ID (e.g. D133)")
    dadd.add_argument("short_name", help="Short name slug")
    dadd.add_argument(
        "status", help="Status (implemented|defined|planned|implemented-poc)"
    )
    dadd.add_argument("description", help="Description")

    dget = dsub.add_parser("get", help="Get one decision by ID")
    dget.add_argument("id", help="Decision ID")

    dshow = dsub.add_parser("show", help="Show last N decisions")
    dshow.add_argument("n", nargs="?", type=int, default=10)

    dresolve = dsub.add_parser("resolve", help="Resolve a decision")
    dresolve.add_argument("id", help="Decision ID")
    dresolve.add_argument(
        "resolution",
        choices=["ticketed", "superseded", "implemented", "wontfix"],
    )
    dresolve.add_argument("--notes", default=None)

    dsub.add_parser("open", help="Show all unresolved decisions")

    # ── channel ──
    cp = subs.add_parser("channel", help="Coordination channel operations")
    csub = cp.add_subparsers(dest="subcmd", required=True)

    cpost = csub.add_parser("post", help="Post a message to the channel")
    cpost.add_argument("message", help="Message content")
    cpost.add_argument("--as", dest="author", default=None, help="Author name")

    cread = csub.add_parser("read", help="Read last N channel messages")
    cread.add_argument("n", nargs="?", type=int, default=20)

    # ── env ──
    envp = subs.add_parser("env", help="Check environment configuration")
    envp.add_argument("--check", action="store_true", help="Print DB URL status")

    return p


def main():
    p = build_parser()
    args = p.parse_args()

    dispatch = {
        "ticket": cmd_ticket,
        "session": cmd_session,
        "decision": cmd_decision,
        "channel": cmd_channel,
        "env": cmd_env,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        p.print_help()
        sys.exit(2)
    handler(args)


if __name__ == "__main__":
    main()
