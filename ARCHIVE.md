# TheIgors — Archive Notice

**Status: Archive** (as of 2026-05-25)

This repository has been converted from an active development repo to a documentation and
support archive. Igor's source code lives in a new home.

---

## What Moved

| What | From | To |
|------|------|----|
| Igor cognition engine | `wild_igor/igor/` | [`UnseenUniversity/devices/igor/`](https://github.com/akienm/UnseenUniversity) |
| Tests | `tests/igor/` | `UnseenUniversity/tests/igor/` |
| Import prefix | `wild_igor.igor.*` | `devices.igor.*` |

**Decision:** `D-igor-into-adc-2026-05-25` — full git history preserved via `git subtree`.

---

## What Stays Here

This repo remains the canonical home for:

- **`lab/`** — design docs, decisions log, CC workflow tools, skills
- **`lab/claudecode/`** — CC workflow tools (cc_queue.py, channel.py, session_manager.py, etc.)
- **`lab/design_docs/`** — architecture decisions, specs, audit reports
- **`lab/design_docs_for_igor/`** — palace nodes, decisions log, shape lock
- **`~/.claude/skills/`** — Claude Code skill definitions (via CLAUDE.md)
- **`papers/`** — research notes and case studies

---

## Where wild_igor/ Went

The `wild_igor/` directory was deleted from this repo. Its contents were
already migrated to `UnseenUniversity/devices/igor/` before deletion.
Full git history for all migrated files is preserved in the UnseenUniversity repo
(migration used `git filter-repo` + `git subtree` to carry commits).

---

## Active Development

Go to **[UnseenUniversity](https://github.com/akienm/UnseenUniversity)** for:
- Igor source code (`devices/igor/`)
- Running Igor
- Filing code bugs and tickets
- Building new devices and rack infrastructure

---

## The Name

TheIgors takes its name from Terry Pratchett's Discworld, where the Igors are a clan of
dedicated servants who share skills, remember everything, and always ask:
*"What shall we try next, mathter?"*

The project continues under the name **UnseenUniversity** — the Discworld institution
where wizards do magic and things go interestingly wrong.
