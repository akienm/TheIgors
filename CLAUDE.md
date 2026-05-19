# TheIgors — Claude Code bootstrap

Canonical rules live in the palace DB, not this file. This shim holds only
what you need **before** you can reach the DB, plus the destructive-action
blocklist that's too dangerous to depend on a DB query.

---

## Read rules on session start

Always pull the palace rules at the start of a fresh session — the full
canonical set lives there, and CLAUDE.md is just the pre-DB bootstrap:

```bash
psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
  "SELECT title, content FROM memory_palace
   WHERE path LIKE 'theigors/rules/%' ORDER BY path" -tA | less
```

Order (top-to-bottom): approach-frame → persona → coding → commits → memory →
database → budget → collaboration → igor-constraints → docs-live-in-code →
safeguards.

`/context-load` pulls these explicitly. During a working session, always
reach for `memory_get(path="theigors/rules/<name>")` for single-node reads
and `memory_search(query="...")` for topic lookups — those are the
frictionless defaults. Read the full palace tree any time with
`SELECT path, title FROM memory_palace ORDER BY path`.

---

## Destructive-action blocklist (honor without DB access)

These are the actions whose consequences are hard enough to reverse that
every one gets its own "Always do X instead" line:

- **Always Akien-review before moving or renaming anything under `brainstem/`.** These files are HIGH-inertia; a silent rename breaks symbol resolution across Igor's cognition.
- **Always protect `~/.TheIgors/Igor-wild-0001/wild-0001.db`.** It's the live DB; deletion loses Igor's working state.
- **Always note what changed and why when editing `.env`.** The env split (CC vs Igor) is load-bearing; silent edits create ghost bugs that take hours to localize.
- **Always create a new commit — never `git commit --amend`.** Amends rewrite history; new commits keep the decision-rollup trace intact.
- **Always push non-force to main.** `git push --force` to main overwrites shared history; only do it with explicit instruction.
- **Always leave `IGOR_TIER5_ENABLED` and `IGOR_ARBITER_ENABLED` off.** Enabling these ships unsafe code paths to production.
- **Always let pre-commit hooks run.** Never use `--no-verify` — the hooks are the last line of defense against committing debris.
- **Always go through `/decided` to write the decisions log.** `decisions_log.dsb` is a structured echo now; direct writes corrupt the chronological record.
- **Always stage files specifically by name.** Name-staging keeps `.env`, `*.db`, and runtime paths under `~/.TheIgors/` out of commits automatically.

---

## Environment split (CRITICAL — pre-DB)

CC uses Claude Max auth — no API key required. Igor's `.env` sets OR routing
and does NOT affect CC. Always treat Igor's `.env` as Igor's environment —
reading it tells you nothing about what CC has in its own env.

---

## What this project is

**Igor is a graph matrix reasoning engine.** Python AI agent, persistent
Postgres memory, local-first inference, progressive autonomy.

- **Repo:** https://github.com/akienm/TheIgors
- **Code:** `wild_igor/igor/`
- **DB:** `Igor-wild-0001` (Postgres)
- **Runtime:** `~/.TheIgors/Igor-wild-0001/`
- **Launch:** `igor` (bash alias, loops on exit 42)

---

## Palace map (where to find everything else)

| Path | What lives there |
|---|---|
| `theigors/rules/*` | working conventions (this shim bootstraps them) |
| `theigors/subsystem_index` | load-bearing subsystems → primary file |
| `theigors/decisions/*` | D### rollups |
| `theigors/tickets` | ticket queue (echo of `clan.memories` tickets subtree) |
| `theigors/slates/*` | daily slate REFERENCE rows |
| `theigors/skills/*` | skill PROCEDURAL rows |

Repo echo of the palace lives at `lab/theigors/` (auto-synced by
`lab/claudecode/palace_sync.py`).

---

## DAEMON EMERGENCY EXIT

DAEMON_EMERGENCY_EXIT=false

When this flag is `true`: **immediately halt all work and exit without doing anything**.
Do not claim any ticket. Do not run any sprint. Do not write any files.
Just print "Emergency exit: DAEMON_EMERGENCY_EXIT is set — halting." and stop.

This is the remote kill switch for worker-daemon sessions.
To activate: set `DAEMON_EMERGENCY_EXIT=true` and commit.
To deactivate: set back to `false` and commit.
The daemon will pick up the change on the next sprint launch (new Claude process each time).

---

## Hierarchy when sources disagree

code > palace > CLAUDE.md > MEMORY.md. Palace is the index; code is the
truth. When palace says X and code says Y, always trust the code and
update the palace.
