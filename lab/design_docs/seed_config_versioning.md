# Versioned Seed Config Pattern — T-versioned-seed-config

**Filed**: 2026-04-18b after two lost-and-rebuilt incidents in one session (watchlist + machines table).
**Status**: shipped for watchlist and machines; extend to other config-shaped state as it surfaces.

## The problem

Some DB-resident state is hand-curated, small, structured, and load-bearing:

- `infra.machines` — fleet routing info (hostname, ip, ollama_model, rank, in_use_hours…)
- `clan.memories WHERE metadata.habit_type = 'watch'` — questions + topics shaping reading extraction

Both drifted/got wiped without a rollback path. Both were rebuilt from Akien's memory.
The recovery story was "hope you remember."

## The principle

**Config-shaped + hand-curated + load-bearing → version-controlled seed file.**

- Source-of-truth: a YAML in `lab/seed/`
- Runtime cache: the Postgres row
- Sync direction: **file → DB** (inverse of the memory palace's DB → file echo)
- History: `git log lab/seed/<name>.yaml`
- Rollback: `git checkout <sha> lab/seed/<name>.yaml && python3 lab/claudecode/seed_<name>.py`

## Why inverse from the palace

The memory palace (`lab/theigors/*.md`) is accreted by cognition — new nodes
land through reading, conversation, habit formation. The palace sync writes
DB → file so git can witness what grew.

Watchlist and machines aren't accreted — they're **composed by the human**.
So the human edits the file, and a seeder upserts that into the DB. The
DB is the runtime cache; the file is the thing.

## What's versioned so far

### Watchlist (GH-299 + recovered 2026-04-18)

- `lab/seed/watchlist.yaml` — 9 questions + 9 topics from Akien's dictation
- `lab/claudecode/seed_watchlist.py` — reads YAML (falls back to embedded snapshot if file missing), upserts as `PROCEDURAL` memories with `habit_type: watch`
- Idempotent via the memory id (`WATCH_Q_NN`, `WATCH_T_NN`)

### Machines (snapshotted 2026-04-18)

- `lab/seed/machines.yaml` — 6 machines (4 online qwen workers + 2 offline niche)
- `lab/claudecode/seed_machines.py` — reads YAML, upserts via `INSERT … ON CONFLICT (hostname) DO UPDATE`
- Deliberately does NOT delete rows missing from YAML. Removal is explicit, not seed-time.

## Future candidates (file if/when they bite)

- CP cornerposts — currently seeded in `main.py`; candidate for `lab/seed/cornerposts.yaml`
- Clan-sheet / identity patterns — if they're rebuildable deterministically, they're config
- Credential references (names, not values) — `CRED_*` memories in main.py

## What stays in the DB only

- Accreted memories (reading deposits, episodic, observations)
- Interpretive edges and co-activation weights
- TWM observations, ring entries
- Activation counts, friction history

These grow organically; YAML would be lossy + noisy.

## Extending the pattern

A new seeded kind:

1. Decide the shape. Small, structured, hand-curated? → YAML. Graph-accreted? → stays in DB.
2. Write `lab/seed/<name>.yaml` with a semver-friendly structure.
3. Write `lab/claudecode/seed_<name>.py` that upserts by stable id.
4. Document an embedded-fallback if the seeder runs before the YAML exists (safety net).
5. Link to this doc from the seeder's docstring.
6. Mention the pattern in CLAUDE.md (or the memory palace) if it's load-bearing enough.

The rule: if losing it would make Akien say "that's scary," it wants a YAML.
