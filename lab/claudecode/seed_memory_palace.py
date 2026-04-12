#!/usr/bin/env python3
"""
seed_memory_palace.py — Populate the memory_palace tree.

T-memory-palace-populate: Create the initial tree structure with signpost nodes.
Each node is a pointer to where information actually lives (code, DB tables,
design docs, tools) — not a copy of that information.

Idempotent: uses ON CONFLICT DO UPDATE so re-running refreshes the seed data.
"""

import json
import os
import sys
from datetime import datetime, timezone


def main():
    db_url = os.environ.get("IGOR_HOME_DB_URL")
    if not db_url:
        print("ERROR: IGOR_HOME_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    import psycopg2

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    updater = "seed_memory_palace"

    # ── Tree definition ──────────────────────────────────────────────────────
    # Each entry: (path, title, content, pointers_list)
    # pointers = list of {type: "...", ref: "..."} dicts
    nodes = [
        # ═══ ROOT ═══
        (
            "theigors",
            "TheIgors Project",
            "Graph matrix reasoning engine. Local-first companion AI that shrinks "
            "cloud dependency as local cognition grows. Goal: self-programming, "
            "self-improving household/swarm agent.",
            [
                {"type": "repo", "ref": "https://github.com/akienm/TheIgors"},
                {"type": "file", "ref": "CLAUDE.md"},
                {
                    "type": "discussion",
                    "ref": "https://github.com/akienm/TheIgors/discussions/62",
                },
            ],
        ),
        # ═══ RULES — behavioral for all agents ═══
        (
            "theigors/rules",
            "Behavioral Rules",
            "Rules agents follow without exception. Coding conventions, safety "
            "limits, collaboration style. CC reads these at session start.",
            [],
        ),
        (
            "theigors/rules/coding",
            "Coding Conventions",
            "Read before editing. Check inertia level. HIGH files need strong "
            "justification. MEDIUM files discuss first. LOW files freely improvable. "
            "Never --no-verify or force-push main.",
            [
                {"type": "file", "ref": "CLAUDE.md"},
                {
                    "type": "note",
                    "ref": "HIGH: brainstem/, memory/models.py, cognition/reasoners/base.py",
                },
                {
                    "type": "note",
                    "ref": "MEDIUM: cognition/, memory/cortex.py, main.py",
                },
                {"type": "note", "ref": "LOW: tools/, dashboard/, word_graph.py"},
            ],
        ),
        (
            "theigors/rules/commits",
            "Commit Discipline",
            "Commit = full cycle (add + commit + pull + push). Autonomous commit "
            "rights: tests pass + no secrets = commit without asking. Never "
            "--no-verify or force-push main. Never commit .env, *.db, or "
            "~/.TheIgors/ paths.",
            [
                {"type": "skill", "ref": "/commit"},
                {"type": "tool", "ref": "gh CLI for PRs/issues"},
            ],
        ),
        (
            "theigors/rules/memory-discipline",
            "Memory Discipline",
            "Verify before trusting memory: grep the code, don't trust 'X was "
            "removed' claims from prior sessions. Check boot timestamp before "
            "claiming code is stale. Use MCP tools (mcp__igor__memory_get/search) "
            "not raw psql for memory queries.",
            [
                {"type": "tool", "ref": "mcp__igor__memory_search"},
                {"type": "tool", "ref": "mcp__igor__memory_get"},
            ],
        ),
        (
            "theigors/rules/database",
            "Database Rules",
            "NO SQLITE anywhere — everything Postgres. db_proxy translates ?→%s "
            "blanket, so use jsonb_exists(metadata, 'key') not metadata ? 'key'. "
            "All DB access through db_proxy, never raw psycopg2 in tools.",
            [
                {"type": "file", "ref": "wild_igor/igor/memory/db_proxy.py"},
                {"type": "table", "ref": "Igor-wild-0001 (Postgres)"},
            ],
        ),
        (
            "theigors/rules/budget",
            "Budget Discipline",
            "Never recommend spending tiers or budget limits. Present numbers, "
            "let Akien decide. Prior bad call cost $2200. CC is flat-rate Pro Max "
            "($100/mo). Igor's OR spend is the meter — minimize that, not CC usage.",
            [],
        ),
        (
            "theigors/rules/collaboration",
            "Collaboration Style",
            "HIGH inertia edits = CC only. Keep going — never offer stopping. "
            "Background work has no timeout. Flag POC code for follow-up tickets. "
            "Proactive suggestions welcomed. Autonomous sprint mode when Akien says "
            "'keep going' or 'not in here today'.",
            [],
        ),
        (
            "theigors/rules/igor-ops",
            "Igor Operations",
            "Never grep for Igor process (use dashboard/channel). Igor instance "
            "dir is ~/.TheIgors/Igor-wild-0001/ (capital I). Machines always "
            "start with 'akien': akiendelllinux, akienyoga9i, akienyogai7 — "
            "never shorten. Igor runs ONLY on akiendelllinux.",
            [
                {"type": "url", "ref": "http://localhost:8080/api/dashboard"},
                {"type": "tool", "ref": "mcp__igor__channel_read"},
            ],
        ),
        (
            "theigors/rules/igor-constraints",
            "Igor Execution Constraints",
            "Igor NEVER calls Anthropic direct (tier 5 inhibited). Use Igor's "
            "systems (gateway, router, logging) — never bypass. code_ref habits "
            "only dispatch 1-required-arg tools. identity_gate fires on read_file "
            "output. New tools must be added to tools/__init__.py.",
            [
                {"type": "file", "ref": "wild_igor/igor/tools/__init__.py"},
                {
                    "type": "file",
                    "ref": "wild_igor/igor/cognition/inference_gateway.py",
                },
            ],
        ),
        # ═══ HISTORY — one unified project history ═══
        (
            "theigors/history",
            "Project History",
            "Single source of truth for project history. Git log has commit "
            "history. decisions_log.dsb has architectural decisions (D001-D360+). "
            "session_manager (Postgres) has session records with key_changes.",
            [
                {"type": "command", "ref": "git log --oneline"},
                {"type": "file", "ref": "lab/design_docs_for_igor/decisions_log.dsb"},
                {"type": "script", "ref": "lab/claudecode/session_manager.py show N"},
            ],
        ),
        # ═══ SLATES — daily work tracking ═══
        (
            "theigors/slates",
            "Daily Slates",
            "Per-day work tracking: planned tickets, ad hoc work, done items. "
            "Written at day start, closed at day end. One file per day.",
            [
                {"type": "dir", "ref": "~/.TheIgors/claudecode/"},
                {"type": "format", "ref": "YYYYMMDD.slate.txt"},
                {"type": "skill", "ref": "/day-close"},
            ],
        ),
        # ═══ NOTES — project-level facts and decisions ═══
        (
            "theigors/notes",
            "Project Notes",
            "Non-rule, non-history project facts: north star, trust framework, "
            "active work, architectural direction.",
            [],
        ),
        (
            "theigors/notes/north-star",
            "North Star",
            "Local-first companion AI, self-improving, household/swarm scale. "
            "Cloud shrinks as local grows. Igor reading + learning → self-programming "
            "→ cloud independence. Every category tracks cloud-escape-rate.",
            [],
        ),
        (
            "theigors/notes/trust-framework",
            "Igor Trust Framework",
            "6 pillars of progressive autonomy. Growing capability = growing "
            "autonomy boundary. HIGH-inertia edits stay with CC until Igor "
            "demonstrates sustained reliability.",
            [],
        ),
        (
            "theigors/notes/active-epics",
            "Active Epics",
            "Claude · Cognition · Training · Operations · Database · Swarm · "
            "Productization. Ticket epic field groups work by long-term theme.",
            [
                {"type": "script", "ref": "cc_queue.py list"},
            ],
        ),
        # ═══ IGOR — agent code map ═══
        (
            "theigors/igor",
            "Igor Agent",
            "Python AI agent with Postgres memory, graph matrix reasoning, "
            "persistent cognition. Runs on akiendelllinux. DB: Igor-wild-0001.",
            [
                {"type": "dir", "ref": "wild_igor/igor/"},
                {"type": "launch", "ref": "igor (bash alias, loops on exit 42)"},
                {"type": "instance", "ref": "~/.TheIgors/Igor-wild-0001/"},
            ],
        ),
        (
            "theigors/igor/cognition",
            "Cognition Pipeline",
            "Inference gateway (tier routing), thalamus (preparse gate), "
            "narrative engine, milieu (VAD state), interruptors, push sources "
            "(boredom/curiosity/goals), consolidation, habit dispatch.",
            [
                {"type": "dir", "ref": "wild_igor/igor/cognition/"},
                {
                    "type": "file",
                    "ref": "wild_igor/igor/cognition/inference_gateway.py",
                },
                {"type": "file", "ref": "wild_igor/igor/cognition/thalamus.py"},
                {"type": "file", "ref": "wild_igor/igor/cognition/narrative_engine.py"},
                {"type": "file", "ref": "wild_igor/igor/cognition/push_sources.py"},
            ],
        ),
        (
            "theigors/igor/memory",
            "Memory System",
            "Cortex (SQLite-compatible Postgres wrapper), ring memory (conversation "
            "buffer), TWM (transient working memory, attentional gating), interpretive "
            "edges, engram trees, word graph (two-tier: words + bigram chunks).",
            [
                {"type": "dir", "ref": "wild_igor/igor/memory/"},
                {"type": "file", "ref": "wild_igor/igor/memory/cortex.py"},
                {"type": "file", "ref": "wild_igor/igor/memory/models.py"},
                {"type": "file", "ref": "wild_igor/igor/memory/db_proxy.py"},
                {
                    "type": "table",
                    "ref": "memories, ring_memory, twm_observations, memory_palace",
                },
            ],
        ),
        (
            "theigors/igor/training",
            "Training & Reading",
            "Reading pipeline: reading_list → book_learner → FACTUAL nodes → "
            "consolidation → INTERPRETIVE → PROCEDURAL habits. Model: qwen2.5:7b "
            "(local free, OR $0.16/book). Trail training via Hebbian edges on "
            "search co-activation (D358).",
            [
                {"type": "dir", "ref": "wild_igor/igor/tools/reading_engine.py"},
                {"type": "file", "ref": "lab/claudecode/book_learner.py"},
                {"type": "table", "ref": "reading_list"},
                {"type": "habit", "ref": "PROC_LIST_ABSORBED_BOOKS"},
            ],
        ),
        (
            "theigors/igor/operations",
            "Operations",
            "Budget tracking, cluster router (cross-machine inference), channels "
            "(web/discord/gmail), dashboard, forensic logging, jobs queue.",
            [
                {"type": "file", "ref": "wild_igor/igor/tools/budget.py"},
                {"type": "file", "ref": "wild_igor/igor/cognition/cluster_router.py"},
                {"type": "dir", "ref": "wild_igor/igor/network/channels/"},
                {"type": "url", "ref": "http://localhost:8080/api/dashboard"},
            ],
        ),
        (
            "theigors/igor/tools",
            "Tool Registry",
            "All Igor tools live in wild_igor/igor/tools/. Register via "
            "registry.register(Tool(...)) at module bottom. Import added to "
            "tools/__init__.py so reasoners pick them up. 150+ tools registered.",
            [
                {"type": "file", "ref": "wild_igor/igor/tools/__init__.py"},
                {"type": "file", "ref": "wild_igor/igor/tools/registry.py"},
                {
                    "type": "doc",
                    "ref": "lab/design_docs_for_igor/capabilities_index.dsb",
                },
            ],
        ),
        (
            "theigors/igor/interruptors",
            "Interruptors",
            "Reflexive checks firing between turns: context_length, cost_budget, "
            "boredom_detector, curiosity, goal_continuation. Each checks cortex "
            "state and pushes to TWM if threshold met.",
            [
                {"type": "file", "ref": "wild_igor/igor/cognition/interruptors.py"},
                {"type": "file", "ref": "wild_igor/igor/cognition/push_sources.py"},
            ],
        ),
        (
            "theigors/igor/inertia",
            "Code Inertia Levels",
            "Self-edit resistance gate. HIGH (0.90+): brainstem/, memory/models.py, "
            "cognition/reasoners/base.py — never edit casually. MEDIUM: cognition/, "
            "memory/cortex.py, main.py. LOW: tools/, dashboard/, word_graph.py.",
            [
                {"type": "file", "ref": "wild_igor/igor/tools/self_edit.py"},
                {"type": "env", "ref": "IGOR_SELF_EDIT_ENABLED"},
            ],
        ),
        # ═══ CLAUDE — CC's section ═══
        (
            "theigors/claude",
            "Claude Code",
            "CC is the primary development tool. Architecture design, sprints, "
            "audits, committing. Flat-rate Pro Max. Uses real Anthropic key "
            "(REAL_ANTHROPIC_API_KEY) — Igor's .env OR routing does NOT affect CC.",
            [
                {"type": "env", "ref": "REAL_ANTHROPIC_API_KEY"},
                {"type": "launcher", "ref": "superclaude / cc.sh"},
                {"type": "dir", "ref": "~/.claude/"},
            ],
        ),
        (
            "theigors/claude/skills",
            "Skills",
            "CC skills live in ~/.claude/skills/<name>/SKILL.md. Current set (15): "
            "context-load, sprint, commit, ticket, note, review, audit, day-close, "
            "savestate, savestateauto, fixit, readigor, deep-audit, test-fix, "
            "validate-files. Haiku routing for mechanical work.",
            [
                {"type": "dir", "ref": "~/.claude/skills/"},
            ],
        ),
        (
            "theigors/claude/mcp",
            "MCP Tools",
            "CC talks to Igor via MCP: mcp__igor__memory_get/search/list_by_type, "
            "channel_read, cc_send, hot_nodes, hot_attractors, traces_get, "
            "request_compaction. Also per-machine: mcp__igor_akiendell__*, "
            "mcp__igor_yoga9i__*, mcp__igor_yogai7__*.",
            [],
        ),
        (
            "theigors/claude/references",
            "External References",
            "Where to find things outside the repo: GitHub issues/PRs, master "
            "plan discussion #62, Linear (if any), live dashboards, Igor's "
            "forensic logs, reading list DB.",
            [
                {"type": "url", "ref": "https://github.com/akienm/TheIgors"},
                {"type": "discussion", "ref": "#62 master plan"},
                {"type": "dir", "ref": "~/.TheIgors/Igor-wild-0001/logs/"},
            ],
        ),
        (
            "theigors/claude/scripts",
            "Lab Scripts",
            "CC-maintained scripts in lab/claudecode/: cc_queue.py (tickets), "
            "session_manager.py (session records), decision_manager.py (decisions "
            "table), github_sync.py, docs_sync.py, channel.py.",
            [
                {"type": "dir", "ref": "lab/claudecode/"},
            ],
        ),
        # ═══ AKIEN — preferences ═══
        (
            "theigors/akien",
            "Akien",
            "Primary developer and project lead. Working conventions: "
            "pre-approve all file edits, discuss plan before big changes. "
            "CC is primary dev tool — avoid aider/Gemini/other LLMs.",
            [],
        ),
        (
            "theigors/akien/interaction-style",
            "Interaction Style",
            "Terse responses preferred. Autonomous sprint mode when he says "
            "'keep going' or 'not in here today'. Proactive best-practice "
            "suggestions welcomed. Never offer stopping as an option.",
            [],
        ),
        (
            "theigors/akien/mission",
            "Akien's Mission",
            "'Change the world.' Local-first AI as counterweight to cloud "
            "monoculture. Igor is the long-term investment in that direction.",
            [],
        ),
    ]

    # ── Insert or update each node ───────────────────────────────────────────
    for path, title, content, pointers in nodes:
        parts = path.rsplit("/", 1)
        parent_path = parts[0] if len(parts) > 1 else ""

        cur.execute(
            """
            INSERT INTO memory_palace
              (path, parent_path, title, content, pointers, updated_at, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (path) DO UPDATE SET
              parent_path = EXCLUDED.parent_path,
              title = EXCLUDED.title,
              content = EXCLUDED.content,
              pointers = EXCLUDED.pointers,
              updated_at = EXCLUDED.updated_at,
              updated_by = EXCLUDED.updated_by
            """,
            [path, parent_path, title, content, json.dumps(pointers), now, updater],
        )

    conn.commit()

    # ── Report ───────────────────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM memory_palace")
    total = cur.fetchone()[0]
    print(f"Seeded {len(nodes)} nodes. Total in palace: {total}")

    cur.execute("SELECT path, title FROM memory_palace ORDER BY path")
    for row in cur.fetchall():
        depth = row[0].count("/")
        indent = "  " * depth
        name = row[0].rsplit("/", 1)[-1]
        print(f"  {indent}{name}/  {row[1]}")

    conn.close()


if __name__ == "__main__":
    main()
