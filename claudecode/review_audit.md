# Codebase Health Review Audit

Run by Worker Claude. One context load covers all checks — batch cost 1×context vs N×context sequential.

Frequency: daily at 2am while `git log --oneline --since='7 days ago' | wc -l` > 5; weekly otherwise.

---

## Checklist

### 1. Dead code
- Functions/classes defined but never called (grep for def/class, cross-check call sites)
- Commented-out code blocks older than 2 sessions
- Imports that resolve to nothing used in the file

### 2. Hardcoded values
- Magic numbers and strings that should be constants or env vars
- Paths that should come from CLAUDE.md-defined locations
- Model names or API keys outside of .env / env vars

### 3. Circular dependencies
- Run: `python3 -c "import wild_igor.igor.main" 2>&1 | grep -i circular`
- Check any new modules added since last audit for import loops

### 4. Unexercised TTL / inertia
- Habits with `twm_ttl_seconds` set — verify the TTL is appropriate for the habit cadence
- Habits with inertia > 0.90 — verify they're intentionally high (not accidentally set)
- TWM entries with ttl_seconds=0 (no expiry) — should be rare; flag for review

### 5. Missing rollback paths
- Self-edit operations without a revert mechanism
- DB writes in tools that have no undo path
- Any new `conn.execute()` calls not inside a try/except with rollback

### 6. Prompt token drift
- Check NE prompt length: `len(narrative_engine._build_prompt("x","x"))` — flag if > 3000 chars
- Check system prompt length via `/metrics` or `system_prompt.py` — flag if > 8000 chars
- Any new f-string injections into prompts that could bloat on real data

### 7. Async timeouts
- `asyncio.wait_for()` calls without timeout — flag any new ones
- `httpx` / `aiohttp` calls without explicit timeout parameter
- Background tasks (daemon threads) with no watchdog or max-runtime guard

### 8. Inhibitory pattern gaps
- Habits that fire on sensitive triggers (ethics, credentials, self-edit) without a validate_against_core() gate
- New tools added since last audit — do they have appropriate guards?
- Any new `exec()` or `eval()` calls anywhere in the codebase

### 9. Architecture drift
- New files in `wild_igor/igor/` — do they have a home in the subsystem DSBs?
- New tools not yet in `capabilities_index.dsb`
- Functions > 80 lines in LOW-inertia files (flag for refactor discussion, not auto-fix)

### 10. Exception hygiene
- Bare `except:` blocks (not `except Exception:`)
- `except Exception: pass` with no log — should at least log to forensic_logger
- Error paths that print but don't log to `~/.TheIgors/logs/`

---

## Output format

Post results as a GitHub comment on discussion #62 or as a new issue if actionable items found.
Format: one line per finding — `[CHECK] file:line — description`.
If nothing found for a check, write `[OK] check_name`.

---

## How to run

```bash
bash ~/TheIgors/claudecode/run_review_audit.sh
```
