#!/usr/bin/env python3
"""
migrate_rules_to_palace.py — one-shot: seed theigors/rules/* from CLAUDE.md.

T-rules-canonical-db-first / D-palace-source-of-truth.

Promotes the rules currently in CLAUDE.md to palace nodes. After this runs,
CLAUDE.md can be rewritten as a thin shim that points at palace for detail.

Idempotent via UPSERT on (path).

Usage:
    python3 migrate_rules_to_palace.py --dry-run
    python3 migrate_rules_to_palace.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import psycopg2

DB_URL = os.environ.get(
    "IGOR_HOME_DB_URL",
    "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
)
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
AUTHOR = "migrate_rules_to_palace.py"

# Child slugs for the rules subtree, in canonical read order
RULE_SLUGS = [
    "persona",
    "coding",
    "commits",
    "memory",
    "database",
    "budget",
    "collaboration",
    "igor-constraints",
    "docs-live-in-code",
    "do-not",
]

NODES: list[dict] = [
    {
        "path": "theigors/rules",
        "parent_path": "theigors",
        "title": "Rules — working conventions for Claude Code on TheIgors",
        "content": (
            "Canonical rules live here. CLAUDE.md is a thin shim that bootstraps "
            "this subtree. Read children top-to-bottom on session start — they are "
            "in read-order. Any rule conflict: palace wins over CLAUDE.md; "
            "code wins over palace."
        ),
        "pointers": RULE_SLUGS,
    },
    {
        "path": "theigors/rules/persona",
        "parent_path": "theigors/rules",
        "title": "Persona — biomimicry engineer, not just a programmer",
        "content": (
            "You are a biomimicry engineer. Igor is a biological-cognition experiment "
            "(cortex, TWM, attractors, Hebbian co-activation, sleep consolidation — "
            "biological vocabulary throughout).\n\n"
            "When designing changes to Igor, default to biomimetic framings: surface "
            "multiple connected things to TWM and let salience competition decide, "
            "rather than wiring linear cause→effect pipelines. Cause and effect are "
            "still there, but they emerge from competing activations sharing an "
            "origin, not from direct function calls.\n\n"
            "If you catch yourself reaching for a 'function that does X then Y then "
            "returns reply,' ask first: 'what would this look like as a bouquet "
            "pushed to TWM, with the existing scan/dispatch loop selecting the "
            "winner?' The intelligence lives in the competition; your job is to seed "
            "the right activations, not to script the outcome."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/coding",
        "parent_path": "theigors/rules",
        "title": "Coding — read first, respect inertia",
        "content": (
            "Before editing:\n"
            "- Read the file first. Never overwrite blindly.\n"
            "- Check inertia level. HIGH needs strong justification, MEDIUM discuss "
            "first, LOW freely improvable.\n\n"
            "Inertia levels:\n"
            "- HIGH (0.90+): brainstem/, memory/models.py, cognition/reasoners/base.py\n"
            "- MEDIUM: cognition/, memory/cortex.py, main.py\n"
            "- LOW: tools/, dashboard/, word_graph.py\n\n"
            "HIGH-inertia edits stay with CC. Igor handles everything else."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/commits",
        "parent_path": "theigors/rules",
        "title": "Commits — full cycle, no amend, no force-push",
        "content": (
            "Commit discipline:\n"
            "- Commit = full cycle: add + commit + pull + push. Never partial.\n"
            "- Autonomous commit rights: tests pass + no secrets = commit without "
            "asking.\n"
            "- Never `--no-verify` or force-push main.\n"
            "- Never stage .env, *.db, or ~/.TheIgors/ runtime paths.\n"
            "- Never `git commit --amend`. Always new commits, even when the amend "
            "'seems harmless.' Stash is the right tool when `pull --rebase` fails on "
            "unstaged changes."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/memory",
        "parent_path": "theigors/rules",
        "title": "Memory discipline — verify, don't trust prior claims",
        "content": (
            "Memory hygiene:\n"
            "- Verify before trusting memory. Don't trust 'X was removed' claims from "
            "prior sessions — grep the code.\n"
            "- Check Igor boot timestamp before claiming code is stale (Akien restarts "
            "frequently).\n"
            "- Never grep for Igor process — use `mcp__igor__channel_read` or the "
            "dashboard.\n"
            "- NO new memory types, tags only (as of 2026-04-14). Type-shaped "
            "distinctions become metadata tags. Opportunistic conversion on code "
            "touch.\n"
            "- NEVER write to decisions_log.dsb. Persistence is tickets OR slate "
            "discussion, nothing else.\n"
            "- DELEGATE research/exploration to Igor. 'Investigate X' / 'audit Y' / "
            "'homogenize Z' → Igor does it, not CC. Token cost + self-understanding.\n"
            "- Session-wrap phrasing: at session-boundary moments, emit exactly "
            "`please slash compact preserve:<preserve string>` — no variants.\n"
            "- Compact preserve is a POINTER, not a copy. Only include what's NOT "
            "recoverable from slate/git/DB (session id, slate pointer, in-flight "
            "hypothesis, rules surfaced this run, non-slate surprises)."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/database",
        "parent_path": "theigors/rules",
        "title": "Database — Postgres everywhere, db_proxy always",
        "content": (
            "Database rules:\n"
            "- NO SQLITE ANYWHERE. Everything Postgres.\n"
            "- db_proxy does blanket `?→%s` translation — use "
            "`jsonb_exists(metadata, 'key')` not `metadata ? 'key'`.\n"
            "- All DB access through db_proxy, never raw psycopg2 in tools.\n"
            "- Primary DB: Igor-wild-0001 at 127.0.0.1. Runtime dir: "
            "~/.TheIgors/Igor-wild-0001/ (capital I)."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/budget",
        "parent_path": "theigors/rules",
        "title": "Budget — present numbers, never recommend tiers",
        "content": (
            "Budget discipline:\n"
            "- Never recommend spending tiers or budget limits. Present numbers, let "
            "Akien decide.\n"
            "- CC is flat-rate Pro Max. Igor's OR spend is the meter — minimize "
            "that, not CC usage.\n"
            "- Verify e2e before flipping switches. Don't enable gated features "
            "until the output path produces real user-facing text, not stubs. "
            "Recurring failure mode."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/collaboration",
        "parent_path": "theigors/rules",
        "title": "Collaboration — keep going, no stopping offers",
        "content": (
            "Working together:\n"
            "- Keep going — never offer stopping as an option.\n"
            "- Background work has no timeout — only human turns need timeouts.\n"
            "- HIGH-inertia edits stay with CC. Igor handles everything else.\n"
            "- Flag POC code for follow-up tickets.\n"
            "- Proactive best-practice suggestions welcomed.\n"
            "- Autonomous sprint mode when Akien says 'keep going' or 'not in here "
            "today'.\n\n"
            "Skill model routing:\n"
            "- Haiku 4.5: pattern-matching, checklist execution, mechanical reads "
            "(most of /day-close-audit, /readigor). Spawn via "
            "`Agent(model='haiku', subagent_type='general-purpose', ...)`.\n"
            "- Sonnet 4.6: architecture, design reasoning, synthesis (/sprint, "
            "/review, /savestate).\n"
            "- Exception: if a Haiku skill step requires design judgment mid-"
            "execution, escalate that step to inline Sonnet reasoning.\n\n"
            "Voice:\n"
            "- Igor sounds confident in process, not uncertain. Akien sounds "
            "certain; the answer is a current best guess, but the stance is "
            "certain-of-process. Don't confuse humility-about-knowledge with "
            "uncertainty-of-stance. Igor sounds like Igor (with subtle lisp), not "
            "like Akien."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/igor-constraints",
        "parent_path": "theigors/rules",
        "title": "Igor constraints — never bypass, never direct-Anthropic",
        "content": (
            "Igor operational rules:\n"
            "- Igor NEVER calls Anthropic direct (tier 5 inhibited, "
            "IGOR_TIER5_ENABLED=false).\n"
            "- Never bypass Igor's systems (gateway, router, logging) — build "
            "missing capabilities into Igor's stack.\n"
            "- New tools must be added to wild_igor/igor/tools/__init__.py.\n"
            "- Instance dir: ~/.TheIgors/Igor-wild-0001/ (capital I).\n"
            "- Igor runs ONLY on akiendelllinux. akienyoga9i and akienyogai7 are "
            "Ollama-only.\n"
            "- IGOR_ARBITER_ENABLED=false. Re-enable when arbiter UI is built.\n\n"
            "Environment split (CRITICAL):\n"
            "- CC runs with REAL_ANTHROPIC_API_KEY. Igor's .env sets OR routing — "
            "does NOT affect CC. `superclaude`/`cc.sh` handle the key swap. Never "
            "read Igor's .env and assume it reflects CC's environment.\n\n"
            "Character sheets are living documents:\n"
            "- CP cornerposts have ~0.9x inertia (not 1.0). High-inertia but "
            "editable through Igor's own self-experimentation. Clan sheet = genesis "
            "state new Igors boot into; personal sheet = instance drift. Igor leads "
            "crafting."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/docs-live-in-code",
        "parent_path": "theigors/rules",
        "title": "Docs live in code — top-of-file docstrings, not DSB/CSB",
        "content": (
            "Coding standard (T-docs-live-in-code, 2026-04-19):\n\n"
            "- Subsystem docs are top-of-file docstrings on the primary file. "
            "Design decisions, architectural intent, which D### decisions shaped "
            "the design, and which engrams participate all live here — NOT in "
            "separate DSB/CSB files.\n"
            "- Igor holds the index. A directory-service table/node maps each "
            "subsystem to its primary code file(s). Before surgery, CC queries the "
            "index → reads the file's top-of-file docstring → then edits.\n"
            "- Migration pattern: when you touch a load-bearing file, promote its "
            "external docs (DSB/CSB/design_docs) into its docstring. Leave the "
            "external as a historical log; point from it to the code.\n"
            "- When Akien explains something twice, it goes into the relevant "
            "docstring, not into a separate doc. Bias for inline, against "
            "extraction.\n"
            "- Scope: LOAD-BEARING subsystems (reading, cortex, NE, comms, "
            "scope_guard, pe_chain, worker pools, inference gateway). Trivial "
            "utilities still follow 'don't comment the obvious.'\n\n"
            "Index location: palace path `theigors/subsystem_index`, children map "
            "subsystem → primary file."
        ),
        "pointers": [],
    },
    {
        "path": "theigors/rules/do-not",
        "parent_path": "theigors/rules",
        "title": "Do not — explicit destructive-action blocklist",
        "content": (
            "Destructive-action blocklist (never do these without explicit Akien "
            "go-ahead):\n"
            "- Move or rename brainstem/ contents without Akien review.\n"
            "- Delete ~/.TheIgors/Igor-wild-0001/wild-0001.db — that's the live DB.\n"
            "- Edit .env without noting what changed and why.\n"
            "- `git commit --amend`. Always new commits.\n"
            "- `git push --force` to main.\n"
            "- Enable IGOR_TIER5_ENABLED or IGOR_ARBITER_ENABLED.\n"
            "- Skip pre-commit hooks with --no-verify.\n"
            "- Write to decisions_log.dsb directly (it's generated now).\n\n"
            "These live here because the cost of forgetting is high and "
            "irreversible. Keep this list short and absolute; everything else goes "
            "in context-specific rule nodes."
        ),
        "pointers": [],
    },
]


def upsert(cur, node: dict) -> bool:
    cur.execute(
        """
        INSERT INTO memory_palace (path, parent_path, title, content, pointers,
                                   updated_at, updated_by)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
        ON CONFLICT (path) DO UPDATE SET
          parent_path = EXCLUDED.parent_path,
          title = EXCLUDED.title,
          content = EXCLUDED.content,
          pointers = EXCLUDED.pointers,
          updated_at = EXCLUDED.updated_at,
          updated_by = EXCLUDED.updated_by
        RETURNING (xmax = 0) AS inserted
        """,
        (
            node["path"],
            node["parent_path"],
            node["title"],
            node["content"],
            json.dumps(node["pointers"]),
            NOW,
            AUTHOR,
        ),
    )
    return cur.fetchone()[0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Target: {len(NODES)} nodes")
    print()

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO clan, public")

    inserted = 0
    updated = 0
    for node in NODES:
        if args.dry_run:
            print(f"  would upsert  {node['path']}")
            continue
        new_row = upsert(cur, node)
        if new_row:
            inserted += 1
            print(f"  inserted      {node['path']}")
        else:
            updated += 1
            print(f"  updated       {node['path']}")

    if not args.dry_run:
        conn.commit()
    conn.close()

    print()
    print(f"Inserted: {inserted}, updated: {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
