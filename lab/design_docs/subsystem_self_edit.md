# Subsystem: Self-Edit & Hot Reload

*Updated: 2026-03-14 | Machine-readable: `design_docs_for_igor/subsystem_self_edit.dsb`*

---

## Overview

Igor can modify his own source code. This is gated, inertia-aware, logged, and auto-committed. The self-edit capability is one of the key steps toward the self-programming epic.

**Current state**: `IGOR_SELF_EDIT_ENABLED=false` — disabled during the cognition stabilization sprint. Re-enable by setting `true` in `.env`.

---

## Inertia Levels

| Level | Files | Rule |
|-------|-------|------|
| HIGH (0.90+) | `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py` | Requires Akien review; arbiter gate; never casually modified |
| MEDIUM (0.60–0.89) | `cognition/`, `memory/cortex.py`, `cognition/reasoners/anthropic.py`, `main.py` | Discuss before editing |
| LOW (0.30) | `tools/`, `dashboard/`, `thalamus.py` | Freely improvable; hot-reloadable |

---

## The Edit Flow

1. Check `inertia_registry.dsb` for the target module
2. Read the file before editing (`read_source_file` — never overwrite blindly)
3. Check `design_docs/` for relevant decisions
4. `patch_source_file` (preferred) or `edit_source_file`
5. Syntax check is automatic — rejected changes don't touch disk
6. `reload_module()` if hot-reloadable; else schedule restart
7. Auto-commit + push to git

---

## patch_source_file (Preferred)

Targeted replacement: old_string → new_string. Syntax-checked before writing. Fails clearly if:
- `old_string` not found (stale read)
- `old_string` matches multiple times (add more context)
- Result has a syntax error (original unchanged)

---

## edit_source_file

Full file rewrite. More dangerous. Use only when a patch can't express the change. Same inertia gates and syntax check apply.

---

## Hot Reload (`tools/hot_reload.py`)

`reload_module(module_name)` — `importlib.reload()` on a loaded module. Tool modules self-re-register automatically on reload.

**Blocked modules** (require restart):
- `brainstem/`
- `memory/models.py` — dataclass defs; `isinstance` breaks on reload
- `memory/cortex.py` — owns the live DB proxy
- `cognition/reasoners/base.py`
- `tools/registry.py` — would wipe all tools
- `tools/hot_reload.py` — itself

**Shortname resolution**: accepts partial names like `tools.filesystem`; resolves if unambiguous.

**Auto hot-reload** (D040): after a successful `patch_source_file` or `edit_source_file`, if `IGOR_HOT_RELOAD=true` and the target module is LOW inertia, `_try_hot_reload()` fires automatically.

---

## Forensic Logging

All self-edit events are logged to `~/.TheIgors/logs/self_edit.log` via `log_self_edit()`. Captures: file, syntax_ok, reason, change_summary, git_hash, blocked status.

Blocked writes (brainstem or gate=false) are logged to `blocked_edits.log`.

---

## Security

- `validate_against_core()`: Haiku semantic check before response delivery. CP1-CP6 violation → ring entry + arbiter at urgency 0.9.
- `brainstem/` writes are hard-blocked regardless of `IGOR_SELF_EDIT_ENABLED`.
- HIGH-inertia edits go to arbiter queue (when `IGOR_ARBITER_ENABLED=true`).

---

## Self-Programming Epic (#206)

The full arc: hot_reload (#207, done) → introspection (#208) → test generation (#209) → self-directed rollback (#210).

Dependency insight: get the system stable first, confirm the `books_realtime` milestone, then start the training run. The training run should reinforce the complete, working behavior — not the work-in-progress.

---

## Decisions

D012, D024, D040, D041, D042
