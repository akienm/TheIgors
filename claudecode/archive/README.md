# claudecode/archive — One-Shot Seed Scripts

These scripts were run once to populate the live Igor DB. They live here for
DB rebuild capability. The **live DB is the source of truth** — do not re-run
these unless rebuilding from scratch.

## Usage

Only re-run if the live DB has been destroyed and you need to rebuild genesis state.
Run them in dependency order (identity → cognition → habits → tools).

## ⚠️ DO NOT RUN

| Script | Reason |
|---|---|
| `seed_resource_gate_habits.DO_NOT_RERUN.py` | PROC_RESOURCE_AWARENESS trigger contains "memory" — causes misfire on memory questions. The live DB has this fixed manually. Re-running will revert the fix. See CLAUDE.md Known Broken section. |

## Scripts here

All `seed_*.py` files seeded one category of Igor's memory/habits. Each is
idempotent only if the target DB is empty — running against a populated DB
will create duplicates.

Run date: 2026-03-17 (all seeded before this date; archived 2026-03-18).
