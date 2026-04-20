# TheIgors — Claude Code bootstrap

Canonical rules live in the palace DB, not this file. This shim holds only
what you need **before** you can reach the DB, plus the destructive-action
blocklist that's too dangerous to depend on a DB query.

---

## Read rules on session start

```bash
psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -c \
  "SELECT title, content FROM memory_palace
   WHERE path LIKE 'theigors/rules/%' ORDER BY path" -tA | less
```

Order (top-to-bottom): persona → coding → commits → memory → database →
budget → collaboration → igor-constraints → docs-live-in-code → do-not.

`/context-load` pulls these explicitly; read the full tree any time with
`SELECT path, title FROM memory_palace ORDER BY path`.

---

## Destructive-action blocklist (honor without DB access)

- Move/rename `brainstem/` contents without Akien review.
- Delete `~/.TheIgors/Igor-wild-0001/wild-0001.db` — live DB.
- Edit `.env` without noting what changed and why.
- `git commit --amend` — always create new commits.
- `git push --force` to main.
- Enable `IGOR_TIER5_ENABLED` or `IGOR_ARBITER_ENABLED`.
- Skip pre-commit hooks with `--no-verify`.
- Write to `decisions_log.dsb` directly — generated now.
- Stage `.env`, `*.db`, or `~/.TheIgors/` runtime paths.

---

## Environment split (CRITICAL — pre-DB)

CC runs with `REAL_ANTHROPIC_API_KEY`. Igor's `.env` sets OR routing and
does NOT affect CC. `superclaude`/`cc.sh` handle the key swap. Never read
Igor's `.env` and assume it reflects CC's environment.

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

## Hierarchy when sources disagree

code > palace > CLAUDE.md > MEMORY.md. Palace is the index, code is the
truth. If palace says X and code says Y, trust the code and update palace.
