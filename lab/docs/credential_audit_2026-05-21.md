# Credential Boundary Audit — 2026-05-21

**Ticket:** T-credential-boundary-audit  
**Decision:** D-articles-synthesis-2026-05-21  
**Auditor:** Claude Code (Sonnet 4.6)  
**Scope:** Static code and config audit for credential-in-context patterns. No credential migration performed here.

---

## Canonical boundary pattern (reference)

`wild_igor/igor/paths.py:52` — `home_db_url` property reads `IGOR_HOME_DB_URL` from the environment and **raises RuntimeError if unset** rather than falling back silently. Docstring notes this was the CP6 credential hygiene move from T-hardcoded-instance-refs.

This is the correct boundary: credentials live at the env-var layer, not baked into source.

---

## Findings

### F1 — Hardcoded DB DSN in ~50+ source files (committed to public git) ⚠️

**Pattern:** `psycopg2.connect("postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001")`  
**Status:** T-hardcoded-instance-refs was closed as "Replace 52 hardcoded refs" but files below were NOT migrated.

**wild_igor/ files (9 active cognition/tool modules):**
- `wild_igor/igor/cognition/activate.py:25`
- `wild_igor/igor/cognition/dreaming.py:30`
- `wild_igor/igor/cognition/focus_state.py:33`
- `wild_igor/igor/cognition/narrative_engine.py:1245` ← HIGH-inertia
- `wild_igor/igor/cognition/playbook.py:27`
- `wild_igor/igor/cognition/proposals.py:23`
- `wild_igor/igor/cognition/watch_problems.py:125`
- `wild_igor/igor/tools/pe_chain_priors.py:27`
- `wild_igor/setup_assets/installer.py:360` (bootstrap context — see F5)

**lab/claudecode/ files (~30+ seed/util scripts):**  
audit_runner.py, audit_telemetry.py, book_learner.py, cc_hook_pending.py, cc_queue.py (×2, silent-fallback pattern), cron_feed_reading.py, debug_session_cli.py, drain_learn_queue.py, map_igor.py, reading_campaign.py, review_manager.py, seed_code_a_ticket.py, seed_coding_sprint_habit.py, seed_ef_questions_tree.py, seed_goal_close_habit.py, seed_layer3_*.py (×7), seed_layer4_*.py (×5), seed_machines.py, seed_output_training_habit.py, seed_pattern_extractor_habits.py, seed_reading_facia.py, seed_routing_habits.py, seed_self_training_habit.py, seed_skill_commit/filter/sprint_engram.py, seed_subsystem_index.py, seed_tool_facia.py, seed_topics_tree.py, seed_watchlist.py, seed_worker_foreman.py, slate_manager.py, sprint_infrastructure_brief.py, ticket_prefix_refit.py

**lab/tools/ and lab/utility_closet/:**
- `lab/tools/build_ebook_index.py:35`
- `lab/utility_closet/failover.py:32` (function default parameter `db_password: str = "choose_a_password"`)

**Risk assessment:**
- "choose_a_password" IS the literal Postgres password (not a placeholder)
- Committed to public GitHub (https://github.com/akienm/TheIgors)
- Mitigating: Postgres is bound to 127.0.0.1 — network exploitation impossible
- Real harm: password rotation requires touching 50+ files; violates paths.py boundary

**Determination: FILE TICKET** → T-dsn-hardcode-completion (finish T-hardcoded-instance-refs)

---

### F2 — cc_queue.py silent env-var fallback (subset of F1) ⚠️

**Pattern:** `os.environ.get("IGOR_HOME_DB_URL", "postgresql://igor:choose_a_password@...")`  
**Locations:** `lab/claudecode/cc_queue.py:130, :383`

cc_queue reads the env var but silently falls back to the hardcoded DSN if unset. paths.py explicitly establishes "no silent fallback" as the boundary rule.

**Determination:** Covered by F1 follow-up ticket.

---

### F3 — pe_chain basket: no credential leakage ✅ ACCEPTABLE

The basket dict carries only ticket data: ticket_id, plan_summary, plan_files, observations, test results, consult_results. No credential values are stored in the basket.

OPENROUTER_API_KEY is read via `os.getenv()` in `_call_cloud_programming()` (pe_chain.py:2885) and used only in HTTP Authorization headers. The key value never flows into the basket, into LLM prompts, or into logged output.

**Determination: ACCEPTABLE** — correct boundary pattern.

---

### F4 — OPENROUTER_API_KEY usage ✅ ACCEPTABLE

All usages read from `os.getenv("OPENROUTER_API_KEY", "")` at call time. Used in HTTP Authorization headers only. Affected files:
- `wild_igor/igor/cognition/inference_gateway.py`
- `wild_igor/igor/cognition/consult.py`
- `wild_igor/igor/cognition/cloud_mode.py`
- `wild_igor/igor/cognition/reasoners/openrouter_reasoner.py`
- `wild_igor/igor/tools/pe_chain.py`
- `wild_igor/igor/tools/template_tools.py`, `openrouter_reasoner.py`, `want_tracker.py`, `browser.py`
- `wild_igor/igor/main.py`

Not committed in source. Lives in Igor's `.env` (gitignored at `wild_igor/.env`).

**Determination: ACCEPTABLE** — correct boundary pattern throughout.

---

### F5 — installer.py bootstrap DSN ✅ ACCEPTABLE

`wild_igor/setup_assets/installer.py:360` writes the hardcoded DSN to the new instance's `.env` file as the initial value during first-start setup. This is the bootstrapping context: before any env var exists, the installer must produce a concrete default. The generated `.env` file is gitignored. The password visible in the installer source is the same "choose_a_password" default; risk is the same as F1 (public git) but the bootstrapping function justifies it.

**Determination: ACCEPTABLE** — bootstrapper context. Still benefits from F1 cleanup ticket.

---

### F6 — docker-compose.yml default password ✅ ACCEPTABLE

`docker-compose.yml:35,61` uses `${POSTGRES_PASSWORD:-choose_a_password}` — templated with env override at both the app env and the Postgres init. Override mechanism is correct docker-compose convention.

**Determination: ACCEPTABLE** — dev/docker pattern; env override is present.

---

### F7 — .claude/settings.local.json ✅ LOCAL-ONLY

Contains `PGPASSWORD=choose_a_password` in `allowedTools` entries and `IGOR_HOME_DB_URL` in the `env` block.

**Gitignored** (`.gitignore` line: `.claude/settings.local.json`). Verified: `git ls-files --error-unmatch` exits 1 — file is NOT tracked.

**Determination: LOCAL ONLY** — no git exposure; acceptable for dev tool allowlist.

---

### F8 — Palace nodes: no credential content ✅ ACCEPTABLE

Palace query for nodes containing "password", "api_key", "choose_a_password", or "connection string" returned only a reference to `IGOR_HOME_DB_URL` as an env var name — no literal credential values.

**Determination: ACCEPTABLE** — palace is clean.

---

### F9 — GitHub Actions ANTHROPIC_API_KEY ✅ ACCEPTABLE

`.github/workflows/claude.yml:37` uses `${{ secrets.ANTHROPIC_API_KEY }}` — standard GitHub Actions secret injection. Not in Python source.

**Determination: ACCEPTABLE** — correct secret-management pattern.

---

## Summary table

| Finding | Description | Determination |
|---------|-------------|---------------|
| F1 | ~50+ files with hardcoded `choose_a_password` DSN in public git | **TICKET** T-dsn-hardcode-completion |
| F2 | cc_queue.py silent env-var fallback | Covered by F1 ticket |
| F3 | pe_chain basket credential content | ACCEPTABLE |
| F4 | OPENROUTER_API_KEY usage pattern | ACCEPTABLE |
| F5 | installer.py bootstrap DSN | ACCEPTABLE |
| F6 | docker-compose.yml default | ACCEPTABLE |
| F7 | settings.local.json (gitignored) | LOCAL ONLY |
| F8 | Palace nodes | ACCEPTABLE |
| F9 | GitHub Actions secrets | ACCEPTABLE |

---

## Follow-up tickets filed

- **T-dsn-hardcode-completion** — Complete T-hardcoded-instance-refs: migrate remaining ~50+ hardcoded DSN refs in wild_igor/ and lab/ to `paths().home_db_url` / `IGOR_HOME_DB_URL` env var pattern; remove silent fallbacks.
