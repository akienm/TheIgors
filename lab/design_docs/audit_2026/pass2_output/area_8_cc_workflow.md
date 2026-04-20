# Pass 2 deep-dive — Claude Code workflow + dev-loop

Integrator area. Every other Pass-2 subagent contributes a "how could we
use CC better?" remit; this area weaves them together and takes the
opinionated swing at what to SHIP/DEFER/DISCARD.

Bias declared upfront: **simplify, delete, consolidate** over "add another
skill." Two vectors of change:
1. **More CC reliance** where a human step today should be a hook or a
   skill that Akien never has to think about (key-swap friction, slate
   merging, env-var export, compact-preserve hand-off).
2. **Less CC reliance** where CC is currently doing compiled-script work
   — context-load's per-session `psql` bulk-read of rules, cc_queue
   orchestration via CLI fan-out from skills, decision_manager's DSB
   file-prepend — these should be one Python call into a shared
   `lab.claudecode.api` module, not CC tokens.

---

## Per-finding verdicts

### Finding 11B-1 — Redundant manager scripts (decision_manager, session_manager, cc_queue, github_sync, docs_sync, palace_sync)

- Verdict: **CONFIRMED_WORSE**
- Blast radius: Every skill invokes at least two of these as subprocesses.
  `/context-load` alone shells out to `session_manager.py` (twice),
  `cc_queue.py`, `channel.py`, and does two `psql` calls. Each is a
  fresh Python interpreter boot, each a new psycopg2 connection, each
  with its own env-var discovery and its own hand-built `IGOR_HOME_DB_URL`
  default. The skill files carry the DB URL hardcoded in **20
  locations across 10 files** (grep confirms). Changing the DB password
  today requires editing 10 skill SKILL.md files, or the password flows
  through in plaintext and "wins" silently because nothing cross-checks.
  Worse: scripts invoke each other by subprocess — `decision_manager.py`
  line 75 calls `Path.home() / "TheIgors" / "claudecode" / "cc_queue.py"`
  which is a **broken path** (the file lives under `lab/claudecode/`).
  The silent `except Exception: pass` at line 83 means this has been
  broken since the lab/ migration with zero visible symptom — every
  /decided invocation has been silently failing its Igor-flush for
  weeks/months. This is the "silent-exceptions-hide-real-failures"
  pattern Pass-1 persona 1 flagged, but instantiated right in the dev
  loop.
- Biomimicry: n/a (dev-loop infra, not cognition).
- Proposed ticket:
  - id: `T-cc-admin-consolidation`
  - title: Consolidate cc-admin scripts into `lab.claudecode.api` module + `igor-admin` CLI
  - size: L
  - tags: [CCWorkflow, Simplify, DevLoop]
  - description: Collapse `cc_queue.py`, `decision_manager.py`,
    `session_manager.py`, `slate_manager.py`, `github_sync.py`,
    `docs_sync.py`, `palace_sync.py`, `review_manager.py`, `channel.py`
    (the CLI layer) into a single `lab/claudecode/api.py` module
    exposing Python functions, plus a single `igor-admin` entry-point
    script (argparse or typer) whose subcommands invoke those functions
    in-process. Shape: `igor-admin ticket add|list|claim|done|block`,
    `igor-admin session start|append-change|finalize`,
    `igor-admin decision add|show|get|resolve`,
    `igor-admin slate render|advance`, `igor-admin palace sync`,
    `igor-admin channel post|read|listen`. Each subcommand is a one-line
    adapter calling `api.<verb>()`. Skills drop from 4-5 subprocess
    invocations per step to one. Shared DB connection (module-level)
    amortises psycopg2 setup. Shared `_db_url()` helper eliminates the
    20 hardcoded URLs in SKILL.md files — skills invoke `igor-admin`
    with no env-var setup because `igor-admin` sets its own defaults.
    Scope boundary: does NOT change what the scripts DO
    (semantic parity with current behaviour — tests guard this), does
    NOT touch `cc_bridge.py` or `utility_closet_server.py` (those
    are daemons, different shape), does NOT remove the old `.py`
    entry points immediately — keep them as 2-line shims calling the
    new api for one release, then delete in a follow-up. Files touched:
    all 9 scripts above + every SKILL.md that references them + the
    broken subprocess call in `decision_manager.py:75`. Tests: a
    functional test for each top-level subcommand round-tripping the DB
    call. Disposal: **SHIP**. This is the highest-leverage change in
    the dev loop — reduces CC per-turn overhead significantly and
    eliminates the current class of silently-broken subprocess calls.

### Finding 11B-2 — /savestate vs /savestateauto proliferation + copy-paste preserve string

- Verdict: **CONFIRMED**. Current state as of 2026-04-20: `/savestate`
  is 20 lines and entirely consists of "run /savestateauto, compose a
  preserve string, then trigger /compact." The preserve string is built
  in /savestateauto at step 6, then /savestate asks CC to *compose a
  fresh one* — violating DRY. /savestateauto's compact-preserve block
  is sealed in a comment box for manual copy-paste.
- Blast radius: Every session close. Copy-paste friction compounds at
  scale. Pass-1 persona 11B flagged this exactly: "The next step would
  be for /compact to read this from a file automatically, making the
  process `savestateauto -> compact` with no copy-paste." A side-effect:
  Akien sometimes runs /savestateauto but forgets the compact, or runs
  /compact without preserve string. Both fail modes lose context.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-savestate-compact-one-shot`
  - title: Merge /savestate + /savestateauto + write preserve-string to disk for auto-pickup
  - size: S
  - tags: [CCWorkflow, Simplify]
  - description: Collapse `/savestate` into `/savestateauto` (the auto
    variant is the real body; /savestate becomes an alias that also
    triggers compaction). Preserve-string emission writes
    `~/.TheIgors/claudecode/pending_preserve.txt` atomically. /compact
    reads that file if present and uses its content (via the existing
    `mcp__igor__request_compaction` if tmux, else prints it). Also:
    unify naming — the "auto" suffix is leftover from a transition
    state (T-savestate-append-change-gap shipped), the canonical name
    is `/savestate` now. Scope: no change to what's captured; just
    eliminate the dual command + the copy-paste step. Files touched:
    `savestate/SKILL.md`, `savestateauto/SKILL.md` (delete;
    redirect to /savestate), any skill referencing /savestateauto
    (/sprint step 10, /day-close step 1+12, /sprint-batch step 6). Old
    `/savestateauto` path safe to delete after one session's worth of
    smoke-test. Disposal: **SHIP**.

### Finding 11B-3 — cc_skills/ directory in lab/claudecode/ is a stale skill graveyard

- Verdict: **CONFIRMED** (Pass-1 did NOT explicitly catch this — gap).
  `ls lab/claudecode/cc_skills/` reveals a parallel skills tree with
  27 entries: `audit`, `commit`, `context-load`, `day-close`,
  `day-close-audit`, `decided`, `deep-audit`, `design`, `export-chat`,
  `filter`, `fixit`, `igor`, `note`, `notethat`, `probe`, `readigor`,
  `review`, `savestate`, `savestateauto`, `slate`, `slateclose`,
  `sprint`, `sprint-batch`, `sprint-minion`, `test-fix`, `ticket`,
  `validate-files`. The active path is `~/.claude/skills/` — this
  `lab/claudecode/cc_skills/` directory is legacy, contains retired
  skill names (`filter`, `notethat`, `probe`, `slate`, `slateclose`,
  `sprint-minion`, `igor`, `audit`), AND mirrors the names of still-
  live skills but at stale versions. Nobody reads this tree, but it
  persists in the repo, is checked into git, appears in `grep`
  searches, and can mislead anyone (including Igor) trying to
  understand "what skills exist." This is the dev-loop equivalent of
  the 58 dead habit code_refs the prior audit caught.
- Blast radius: Tiny at runtime (nothing reads it), large at comprehension
  (a grep for "SKILL.md" returns 40+ results, half of them junk). Also
  the directory pollutes the `subprocess`-callable Python path — if any
  future skill accidentally imports from there it'll use stale logic.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-retire-cc-skills-dir`
  - title: Delete lab/claudecode/cc_skills/ (stale skill copies, never read)
  - size: S
  - tags: [CCWorkflow, DeadCode, Cleanup]
  - description: The folder `lab/claudecode/cc_skills/` is a legacy
    mirror of the active skill set at `~/.claude/skills/`. It is not
    referenced by any live code path — `claude` only reads from
    `~/.claude/skills/`. Remove the directory. Before deletion:
    diff against `~/.claude/skills/` and confirm no valuable history is
    being lost (for any skill NOT in the active set —
    `filter`, `notethat`, `probe`, `slate`, `slateclose`,
    `sprint-minion`, `igor`, `audit` — capture their SKILL.md content
    in a single `lab/design_docs/retired_skills.md` archive file for
    historical reference, then delete). Scope: repo hygiene only. No
    behaviour change. Files touched: removal of 27 SKILL.md files +
    their directories. Risk: near-zero (unread path). Disposal: **SHIP**.

### Finding 11B-4 — cc_queue.py as CLI brittleness + queue.json 1.1MB echo

- Verdict: **CONFIRMED**. `queue.json` is 1.1MB and regenerated on
  every `_save()` call. Each `cc_queue.py` subcommand loads all tickets
  from Postgres, mutates one field, then upserts **every ticket** back
  to clan.memories (the N+1 pattern Pass-1 DBA persona flagged at
  `cc_queue.py _save()`). The JSON echo exists solely for `github_sync`
  and Igor's tickets-subtree read path — both of which could read from
  clan.memories directly. The skills invoke `cc_queue.py list | grep
  "⚪\|🟡"` (emoji grep) which is brittle — an emoji change breaks
  every skill silently. And worker_daemon.sh polls the queue as a
  shell script, shelling out to `cc_queue.py list` on an interval.
  Pass-1 cross-cut 11B's "cc_queue.py as CLI brittleness" was exactly
  right.
- Blast radius: Touches the ticket claim→work→close cycle core. The N+1
  write amplifies with ticket count (currently ~400 tickets in queue);
  every close rewrites all 400 rows. Emoji-grep is in /sprint step 1,
  /ticket step 1, /context-load step 5.5. Worker daemon polls 100s of
  times a day.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-queue-api-no-json-echo`
  - title: Replace queue.json echo with direct DB reads; fix cc_queue N+1 writes; structured status API
  - size: M
  - tags: [CCWorkflow, DB, Performance]
  - description: (1) Delete `queue.json` regeneration — downstream
    consumers (`github_sync.py`, Igor tickets subtree) read from
    `clan.memories` directly. (2) Change `cc_queue.py._save()` to
    single-row UPSERT of only the mutated ticket, not all tickets.
    (3) Replace emoji-grep in skills with a structured status query
    via the new `igor-admin` CLI (see T-cc-admin-consolidation) —
    `igor-admin ticket next --status pending` returns a clean id/title
    list. (4) `worker_daemon.sh` switches from polling shell to a
    LISTEN/NOTIFY pattern on a `ticket_available` Postgres channel,
    NOTIFY fired inside `cc_queue._save()` when a ticket transitions
    to pending. Scope boundary: does NOT change ticket shape, does
    NOT change queue semantics. Files touched: `cc_queue.py`,
    `worker_daemon.sh`, `sprint/SKILL.md`, `ticket/SKILL.md`,
    `context-load/SKILL.md`, `github_sync.py` read path. `queue.json`
    safe to delete immediately after grep confirms no unreviewed
    consumer. Disposal: **SHIP** (small). This also sets up the
    LISTEN/NOTIFY pattern Pass-1 DBA persona recommended for TWM
    polling — proving the pattern in the dev-loop first is lower-risk
    than proving it in cognition.

### Finding 11B-5 — Command noise in skill bash blocks burns context

- Verdict: **CONFIRMED_NARROWER**. Skills use `| tail -20` consistently
  in newer writes (pytest, git log, etc.) and that's good. The bigger
  offender is `/context-load` step 2b which dumps the **entire palace
  tree** — `SELECT path, title FROM memory_palace ORDER BY path`.
  Palace currently has 60+ nodes. Every session start pays that cost
  even when CC could cache the tree across sessions. Step 2a dumps
  `content` of every rule node too. Total context-load cost:
  rough-measured ~2000 tokens of which ~1500 are rules and palace
  tree. Pass-1 called this out exactly: "hash the rules, verify on
  subsequent runs, save thousands of tokens per session."
- Blast radius: Every session start. Multiplied by Akien's daily
  session count. Real OR $ cost if CC were on paid tier (CC is flat-
  rate Pro Max, but the context-window cost is real — every 2000
  tokens at session start means 2000 fewer tokens available for work).
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-context-load-rule-hash`
  - title: Cache palace rule-content by hash across sessions; context-load reads hash-only on hit
  - size: S
  - tags: [CCWorkflow, Tokens, Simplify]
  - description: `/context-load` step 2a currently loads all rule
    contents every session. Change: compute a hash of
    `SELECT path, md5(content) FROM memory_palace WHERE path LIKE
    'theigors/rules/%'` — one hash per rule plus a composite over all.
    Write the composite hash to `~/.TheIgors/claudecode/rules_hash.txt`
    after a successful load. On subsequent context-loads: compute
    current composite, compare. If unchanged: just print "rules
    unchanged since last session (hash=abc123)" — the actual rule
    content stays resident in CC's training from recent context. If
    changed: do the full load, and tell CC **which rules changed**
    (the per-path hash diff pinpoints it). Step 2b (tree listing) —
    same treatment: hash the tree, skip re-printing if unchanged.
    Scope: token budget optimization, no behaviour change. Files
    touched: `context-load/SKILL.md`, new state file under
    `~/.TheIgors/claudecode/`. Disposal: **SHIP** (small).

### Finding 11B-6 — Haiku vs Sonnet model audit across skills — gaps

- Verdict: **CONFIRMED**. Current state:
  - `model: haiku`: day-close-audit, design, export-chat, readigor,
    review (5 skills)
  - `model: sonnet`: decided, fixit, sprint-batch (3 skills)
  - **no model declared** (defaults to conversation model, usually
    Sonnet): commit, context-load, day-close, note, savestate,
    savestateauto, sprint, test-fix, ticket, validate-files (10 skills)
  Of the 10 undeclared: `commit`, `note`, `savestate`, `savestateauto`,
  `ticket`, `validate-files` are purely mechanical (file ops, DB
  upserts, git commands) — Haiku-shaped. `context-load` is a
  checklist execution — Haiku-shaped. `sprint` and `test-fix` need
  design judgment mid-execution so Sonnet is correct. `day-close` is a
  wrapper that calls day-close-audit (Haiku already) + mechanical
  git/db steps — Haiku with Sonnet-escalation for step 17-style
  judgment. Estimated OR $ savings from switching 7 skills to Haiku:
  ~70% of current CC cost on those invocations (per Pass-1 11B's
  "~10x cost savings on mechanical work" framing).
- Blast radius: Pure cost reduction, no behaviour risk if per-skill
  judgment is correct.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-skill-model-audit-haiku`
  - title: Annotate all skill frontmatter with explicit model choice (Haiku default, Sonnet where design-reasoning required)
  - size: S
  - tags: [CCWorkflow, Cost, Simplify]
  - description: Walk every SKILL.md under `~/.claude/skills/`. Add
    explicit `model:` to frontmatter. Apply the rule: "if the skill is
    pure checklist-execution + shell commands + DB calls, model:
    haiku. If the skill requires design judgment mid-flight, model:
    sonnet. If it's a thin wrapper around other skills, inherit the
    most-expensive called skill's model, or declare `model: haiku`
    with a `model_exception` note (already used in day-close-audit)."
    Concrete expected outcome:
    - Haiku: commit, context-load, note, savestate (→ merged into
      savestateauto per T-savestate-compact-one-shot), ticket,
      validate-files, day-close (with exception for step 17-style
      simplification review).
    - Sonnet: sprint, sprint-batch, decided, fixit, test-fix.
    - Opus (never — keep Opus for 1M-context audits like this one,
      not dev loop).
    Scope: model-only change; no skill body edits. Files touched: all
    10 undeclared skills. Disposal: **SHIP** (small).

### Finding 11B-7 — `git pull --rebase` + venv activation duplicated across skills

- Verdict: **CONFIRMED**. `source venv/bin/activate` appears in 5
  skills (/commit, /sprint, /sprint-batch, /test-fix, /day-close-audit),
  `git pull --rebase` in 4 skills. Both are "shared setup" that
  sprint-batch already factored out as a single step — but stand-alone
  skills re-declare. Worse: each skill builds its own env-var
  declaration for IGOR_HOME_DB_URL. Inconsistent.
- Blast radius: Minor per invocation, but the duplication is the
  anti-pattern — a password change or venv move requires editing N
  SKILL.md files.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-skill-shared-setup-helper`
  - title: Extract shared setup (venv, DB URL, git-pull) into `igor-admin env` one-shot invoked from skills
  - size: S
  - tags: [CCWorkflow, Simplify]
  - description: Add `igor-admin env --ensure` subcommand (lands under
    T-cc-admin-consolidation) that: activates venv, exports
    IGOR_HOME_DB_URL from a single canonical source (`.env` fallback),
    runs `git pull --rebase origin main`. Returns a dotenv-shaped
    block. Every skill's "shared setup" block becomes one line:
    `eval "$(igor-admin env --ensure --for=sprint)"`. Different skills
    can ask for slight variants (`--for=sprint` skips the pull,
    `--for=commit` includes it). Scope: collapse duplication; no
    behaviour change. Files touched: the 5 shared-setup skills + new
    subcommand. Safe to delete old blocks immediately after
    replacement. Disposal: **SHIP** (follows T-cc-admin-consolidation).

### Finding 11B-8 — Palace echo at lab/theigors/ is a 4th source of truth (Pass-1 11A)

- Verdict: **CONFIRMED**. Pass-1 called this out in persona 11A; it
  belongs in area-8 because it's a CC-workflow touchpoint. The palace
  DB is canonical; `palace_sync.py` writes `lab/theigors/*.md` as
  repo-committed echo. This is fine AS LONG AS the echo is strictly
  one-way and never read back. But `context-load/SKILL.md` reads from
  the **DB** (correct), while some manual grepping by CC during work
  may hit the **files** (wrong). And if `lab/theigors/` drifts because
  `palace_sync.py` isn't run, CC gets stale state when grepping the
  repo. Also: `palace_sync.py` deletes orphan files (line 141-146) —
  destructive operation that runs unguarded.
- Blast radius: Repo drift. Confusion about source-of-truth. Silent
  destructive deletion possible if palace nodes go missing due to bug.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-palace-echo-readme-only`
  - title: Clarify palace repo echo is generated-read-only; guard palace_sync deletes; auto-run on pre-commit
  - size: S
  - tags: [CCWorkflow, Docs, Palace]
  - description: Three changes. (1) Add a top-level note to
    `lab/theigors/README.md` + every generated file header: "This file
    is generated by `lab/claudecode/palace_sync.py` — do not edit; edits
    will be overwritten on next sync. Source-of-truth is the
    `memory_palace` Postgres table." The current README says "auto-
    synced" but not strongly enough. (2) Guard the orphan-delete logic
    in `palace_sync.py`:146 — if the deletion count exceeds 10% of
    existing nodes, bail with an error and require `--force-delete`;
    log every deletion. Prevents a buggy palace query from wiping the
    repo echo. (3) Wire `palace_sync.py` into a pre-commit hook (or
    the igor-admin daily task) so it runs before any commit that
    touches palace-related code, keeping the echo from drifting. Scope:
    hygiene + safety. Files touched: `palace_sync.py`,
    `lab/theigors/README.md`, `lab/claudecode/hooks/pre-commit/`.
    Disposal: **SHIP** (small).

### Finding 11B-9 — CLAUDE.md + MEMORY.md + palace three-layer shim (Pass-1 11A)

- Verdict: **CONFIRMED_NARROWER**. The recently-rewritten CLAUDE.md
  (commit current session) is the correct shape — thin bootstrap,
  delegates to palace. MEMORY.md is also thin now, pointing to palace.
  The drift Pass-1 flagged was pre-rewrite; the current files are in
  good shape. Remaining narrow concern: `MEMORY.md` explicitly links
  to feedback files under `.claude/projects/-home-akien-TheIgors/memory/`
  that are local-only, not in palace. This is a fifth tier of truth
  (palace, CLAUDE.md, MEMORY.md, feedback_*.md, code). The feedback
  files should be promoted to palace nodes.
- Blast radius: Every session's MEMORY.md load. The feedback files
  aren't read directly by CC (the memory system summarises them into
  MEMORY.md), but they ARE the authoritative source for each rule —
  palace should be.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-feedback-files-to-palace`
  - title: Migrate .claude feedback_*.md rules into palace `theigors/rules/feedback/`
  - size: S
  - tags: [CCWorkflow, Palace, Simplify]
  - description: The `.claude/projects/-home-akien-TheIgors/memory/`
    directory contains feedback files (`feedback_no_amend.md`,
    `feedback_no_decisions_log.md`, etc.) that MEMORY.md links to.
    These are rule-shaped — they belong in palace under
    `theigors/rules/feedback/<name>` so they're queryable by
    `palace_read` + survive migrations + flow through the existing
    rule-hash cache (T-context-load-rule-hash). Migrate each feedback
    file to a palace node; MEMORY.md link-set becomes palace-path set.
    Scope: content move; no semantic change. Files touched: each
    feedback_*.md + MEMORY.md + a one-shot migrate script. The old
    feedback files remain as a historical log; delete after one
    month's verification. Disposal: **SHIP** (small).

### Finding 11B-10 — Inertia-label enforcement is string-matching

- Verdict: **CONFIRMED** (Pass-1 AI-Safety persona 8 caught this from
  the safety angle; for CC-workflow the concern is that
  HIGH/MEDIUM/LOW labels drift). `scope_guard.py` implementation
  uses string prefix matching. Skills like `/review` and `/decided`
  call out HIGH-inertia files by string comparison too. If a file is
  renamed (even `memory/models.py` → `memory/memory_models.py`) every
  enforcement path silently reverts to LOW-inertia treatment. The
  CC-workflow angle: no skill has a self-test that "my inertia table
  still matches the subsystem_index."
- Blast radius: Safety-critical. A move/rename under `brainstem/` or
  any HIGH-inertia path would silently flip enforcement off.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-inertia-enforcement-from-palace`
  - title: Store inertia labels in palace `subsystem_index` metadata, not string prefixes
  - size: M
  - tags: [CCWorkflow, Safety, Palace]
  - description: Every subsystem in the palace `subsystem_index`
    already has pointer metadata. Add an `inertia` field
    (`HIGH | MEDIUM | LOW`) to each. Change `scope_guard.py` and the
    `/review` + `/decided` + `/day-close-audit` skills to query palace
    for inertia by file path rather than prefix-match. When a file
    moves, palace is updated at the same time (since palace tracks the
    subsystem's primary file), and enforcement follows automatically.
    Add a `day-close-audit` step that diffs palace inertia labels
    against the rules file — drift = finding. Scope: path-indirection
    change. Files touched: `scope_guard.py`, `review/SKILL.md`,
    `decided/SKILL.md`, `day-close-audit/SKILL.md`, palace
    subsystem_index nodes. Touches `scope_guard.py` which is MEDIUM
    inertia, so worth a quick Akien-review before filing. Disposal:
    **SHIP**.

### Finding 11B-11 — Dead skill references and stale script references

- Verdict: **CONFIRMED** (the 58-dead-code_refs analogue for skills).
  Findings from grep:
  - `slate_manager.py` (429 lines) is referenced only by the stale
    `cc_skills/slateclose/SKILL.md`. The active `day-close/SKILL.md`
    and `context-load/SKILL.md` write to slate files directly with
    bash heredocs — `slate_manager.py` is functionally orphaned but
    still imports-check-clean. Dead.
  - `decision_manager.py:75` has a broken subprocess call (missing
    `/lab/`) silently swallowed by `except Exception: pass`. Flagged
    under 11B-1.
  - `cc_queue.py cmd_inject` is deprecated (worker daemon replaced
    xdotool). Still in COMMANDS dict. Should be removed.
  - `cc_queue.py cmd_needs_review`, `cmd_set_worker`, `cmd_set_epic`
    — each referenced by at most one skill or script. Audit whether
    they're live.
  - `channel.py listen` mode — not called by any skill or script
    (grep confirms); only used ad-hoc by Akien. Low-value dead code.
  - `export_chat.py` hardcodes `/home/akien/TheIgors/claude_chat_logs`
    — Pass-1 persona-1 finding, relevant here because `/export-chat`
    is a CC skill that inherits the breakage.
- Blast radius: Script-maintenance burden. Nothing runtime-critical
  except for the silent-swallow of `decision_manager.py:75`.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-cc-script-dead-code-sweep`
  - title: Sweep dead/orphan functions + broken subprocess calls in lab/claudecode/ scripts
  - size: S
  - tags: [CCWorkflow, DeadCode, Cleanup]
  - description: Targeted cleanup. (1) Delete `slate_manager.py`
    (replaced by inline bash heredocs in skills; consumer path
    verified absent). (2) Fix `decision_manager.py:75` path bug AND
    remove the bare except:pass around the subprocess call; if Igor
    flush fails, log it. (3) Remove `cc_queue.cmd_inject` + its
    COMMANDS entry. (4) Audit `cc_queue.cmd_set_epic`,
    `cmd_needs_review`, `cmd_set_worker` — keep if called, delete if
    not (grep the active skill set + seed scripts). (5) Parameterize
    `export_chat.py` output dir via env var with
    `~/TheIgors/claude_chat_logs/` default, so it's not user-hostile
    for a different checkout. Scope: pure removal + two small fixes.
    Files touched: 5 scripts. Disposal: **SHIP**.

### Finding 11B-12 — Slate section-order + 20260420a slate split (Pass-1 gap)

- Verdict: **CONFIRMED_NARROWER** (Pass-1 didn't catch; discovered in
  runtime state). `ls ~/.TheIgors/claudecode/` shows both
  `20260420.slate.txt` and `20260420a.slate.txt` — two slates for one
  day. `context-load/SKILL.md` only reads
  `$(date +%Y%m%d).slate.txt` (no suffix), so the `a` suffix slate
  is orphaned. Manual Akien workflow of "second slate today" is not
  captured by the skill path.
- Blast radius: Narrow — only affects multi-slate days. But every such
  day means the second slate is invisible to automation.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-multi-slate-per-day`
  - title: Support multiple slates per day (YYYYMMDDa, b, c) as first-class in context-load + slate tooling
  - size: S
  - tags: [CCWorkflow, Slate]
  - description: Update the slate-reading path in /context-load,
    /day-close, /sprint-batch `today-slate` selector. If multiple
    slate files exist for today (`YYYYMMDD.slate.txt`,
    `YYYYMMDDa.slate.txt`, etc.), read them all and concatenate, most-
    recent last (alphabetical-by-suffix is fine). /slateclose (if
    preserved — see 11B-3) auto-names the next as the next letter.
    Scope: multi-slate support. Files touched: context-load,
    day-close, sprint-batch, slate file naming conventions. Disposal:
    **DEFER** — unclear if Akien's workflow really needs this or if
    yesterday's `20260420a` was a one-off. Investigate with Akien
    first; ticket kept for record.

### Finding 11B-13 — queue.json pre-palace-migration backup retained at 1.1MB

- Verdict: **CONFIRMED** (not in Pass-1). `ls -la ~/.TheIgors/cc_channel/`
  shows `queue.json.pre-palace-migration` (1.1MB) and `queue.json.bak`
  (145KB) sitting in runtime alongside the live `queue.json`. These
  are migration artifacts. Never referenced by any script (grep
  confirms). Pure disk waste but also invitation-to-misuse: a future
  skill that shells to `queue.json.*` glob would pull stale state.
- Blast radius: Zero runtime, minor hygiene. But — these SHOULD be in
  `~/.TheIgors/archive/` not `cc_channel/`.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-cleanup-queue-backup-artifacts`
  - title: Remove queue.json.bak + queue.json.pre-palace-migration from live runtime dir
  - size: S
  - tags: [CCWorkflow, Cleanup]
  - description: Delete or archive `~/.TheIgors/cc_channel/queue.json.bak`
    and `~/.TheIgors/cc_channel/queue.json.pre-palace-migration`. If
    they hold diagnostic value (e.g. pre-migration ticket rows the
    palace migration dropped), move to `~/.TheIgors/archive/` with a
    dated filename. Add a /validate-files check that flags any
    `*.bak` or `*.pre-*` file in runtime runtime dirs. Scope: one-shot
    cleanup + audit check. Disposal: **SHIP** (trivial).

### Finding 11B-14 — Hook infrastructure minimal; missed opportunities

- Verdict: **CONFIRMED_WORSE** (Pass-1 11B hinted; going deeper here).
  Current hooks: `lab/claudecode/hooks/pre-commit/` is empty.
  `cc_hook_pending.py` is a UserPromptSubmit hook (injects channel
  messages into CC). That's the only live hook. Opportunities CC is
  missing:
  - **PostToolUse on Bash:** could auto-append tool output to session
    `tool_outputs` (session_manager.py already has
    `append-tool-output` command — no hook invokes it). This is why
    `tool_outputs` column is mostly empty.
  - **SessionStart:** could auto-run `igor-admin env --ensure` (per
    T-skill-shared-setup-helper) instead of each skill re-doing it.
  - **SessionEnd:** could auto-run /savestate instead of relying on
    Akien to remember.
  - **Pre-compact:** could auto-write `pending_preserve.txt` (per
    T-savestate-compact-one-shot) as a fail-safe.
  - **Pre-commit (repo):** catches `decisions_log.dsb` direct writes,
    catches `.env` stage, catches `*.db` stage — every rule the
    CLAUDE.md blocklist names, as a hook rather than CC-enforced.
- Blast radius: Every session relies on Akien/CC to manually honor
  rules. Hook enforcement is free-once-written, forever after.
- Biomimicry: n/a (but note: hooks as "autonomic reflexes" is a
  biomimetic framing — they should never require cognition).
- Proposed ticket:
  - id: `T-cc-hook-autonomics`
  - title: Add Claude Code hooks for SessionStart, SessionEnd, PostToolUse, pre-commit enforcement
  - size: M
  - tags: [CCWorkflow, Hooks, Safety]
  - description: Four hooks to add via `~/.claude/settings.json`:
    (1) `SessionStart` — run `/context-load` automatically + export env
    vars for the session.
    (2) `SessionEnd` — run `/savestate` automatically (fallback: if
    CC already ran it, no-op via hash check).
    (3) `PostToolUse` filter on Bash — parse tool output, call
    `session_manager.py append-tool-output` (via `igor-admin` post-
    consolidation) with a one-line summary so tool_outputs column
    actually populates for crash recovery (which was the whole point
    of the column).
    (4) Git repo `pre-commit` — reject staged `.env`, `*.db`,
    `~/.TheIgors/` runtime paths, direct writes to
    `decisions_log.dsb`, use of `git commit --amend` (rule violations
    per CLAUDE.md).
    Scope: autonomic rule-enforcement. Files touched:
    `~/.claude/settings.json` (via update-config skill),
    `lab/claudecode/hooks/pre-commit/*.sh`. The update-config skill
    is the right vehicle for the settings.json edits. Disposal:
    **SHIP** — these are pure upside, zero cognitive cost.

### Finding 11B-15 — superclaude + cc.sh environment-key handoff is CC-invisible

- Verdict: **NEEDS_RUNTIME** (cannot fully verify statically). CLAUDE.md
  says: "`superclaude`/`cc.sh` handle the key swap. Never read Igor's
  `.env` and assume it reflects CC's environment." The handoff is a
  shell-script workflow CC has no visibility into. If `superclaude`
  fails to export `REAL_ANTHROPIC_API_KEY`, CC runs with whatever
  leaked into env from Igor — no warning until something fails. A
  best-case outcome would be CC at session start checks
  `os.environ.get("REAL_ANTHROPIC_API_KEY")` and asserts it's set,
  distinct from Igor's key, before anything else runs. But `context-
  load/SKILL.md` does not check this today.
- Blast radius: Mis-routing of CC calls to OpenRouter (Igor's tier) is
  a silent cost leak and potentially a compliance concern.
- Biomimicry: n/a.
- Proposed ticket:
  - id: `T-cc-env-split-startup-check`
  - title: context-load step 0 — verify REAL_ANTHROPIC_API_KEY is set and != Igor's OR key
  - size: S
  - tags: [CCWorkflow, Safety]
  - description: Add a Step 0 to `/context-load`: read
    `$REAL_ANTHROPIC_API_KEY` (must be non-empty, must start with
    `sk-ant-`), read `$OPENROUTER_API_KEY` (must be empty or else warn
    loudly — Igor's key leaked into CC env), confirm the key handoff
    from `superclaude` was clean. Output a one-line "env: CC key OK,
    Igor key absent" on success, or surface the failure to Akien
    inline. Scope: startup invariant check. Files touched:
    `context-load/SKILL.md`. Disposal: **SHIP** (trivial, high value).

### Finding 11B-16 — `/ticket` skill is thin, `/decided` is load-bearing — but both duplicate JSON-file-to-stdin pattern

- Verdict: **CONFIRMED_NARROWER**. `/ticket` writes JSON to
  `/tmp/ticket.json` then `cc_queue.py add /tmp/ticket.json`. `/decided`
  writes to `/tmp/decided_batch_<id>.json` then `cc_queue.py add`. Same
  pattern, tmp-file round-trip. Should be stdin or API call.
- Blast radius: Minor friction per invocation.
- Proposed ticket:
  - id: `T-ticket-add-stdin`
  - title: cc_queue add via stdin or API, not /tmp file round-trip
  - size: S
  - tags: [CCWorkflow, Simplify]
  - description: Extend `cc_queue.py add` (pre-consolidation) or
    `igor-admin ticket add` (post) to accept `--stdin` and read JSON
    from stdin. Update /ticket + /decided to pipe JSON directly
    instead of writing `/tmp/*.json` first. Eliminates tmp-file race
    conditions in concurrent sessions and the debris. Scope: CLI arg
    addition. Disposal: **SHIP** (trivial, rolls into
    T-cc-admin-consolidation naturally).

---

## Pass 1 gaps (findings Pass 1 missed in your area)

### Gap 1 — `cc_queue.py flush_session` vs `session_manager.py append-change` race

- Severity: **medium**
- Biomimicry: n/a
- Evidence: `/savestateauto/SKILL.md` step 2 calls
  `cc_queue.py flush_session` (which posts to Igor's
  `/api/cc_send`), then step 3 calls `session_manager.py append-change`
  (which writes to `infra.sessions.key_changes`). These two record
  "what happened" to different stores. If step 2 succeeds but step 3
  fails (DB down during the 5-minute window between Akien's local
  Postgres restart and full recovery), the session record misses the
  change but Igor's channel has it. After compact, neither CC (who
  reads session record) nor Akien (who reads channel) has a
  consistent picture. Docstring for /savestateauto acknowledges
  "flush_session only posts to the Igor channel; it does not touch
  infra.sessions.key_changes" — but doesn't address the atomicity.
- Proposed ticket:
  - id: `T-savestate-atomic-flush`
  - title: Make savestateauto flush + append-change atomic (one DB transaction or idempotent replay)
  - size: S
  - tags: [CCWorkflow, Data]
  - description: Either wrap both writes in a single Postgres
    transaction (flush_session's channel write is already DB-backed
    under `channel_messages`), OR make append-change idempotent and
    auto-replay from channel_messages on next context-load if the
    session record is missing a change. Second option is more robust.
    Disposal: **SHIP**.

### Gap 2 — `igor_mcp.py` surface drift — 975 lines, ≥20 tools exposed

- Severity: **medium**
- Biomimicry: n/a
- Evidence: `igor_mcp.py` is 975 lines (one module) with ≥20 MCP
  tools registered. Every tool is ~30-50 lines of type-schema +
  SQL. No tests. No registration validation against an MCP-tool
  manifest. If a tool's SQL returns an unexpected shape, the error
  bubbles up through stdio to Claude Code with no observability. A
  Pass-1-gap for THIS area because the MCP surface IS the primary
  CC-to-Igor interface for anything beyond `cc_send`.
- Proposed ticket:
  - id: `T-igor-mcp-modularize`
  - title: Split igor_mcp.py into per-tool files + add a tool-manifest test
  - size: M
  - tags: [CCWorkflow, MCP, Tests]
  - description: Break `igor_mcp.py` into `igor_mcp/__init__.py`
    (server + list_tools loop) + `igor_mcp/tools/<name>.py` per tool.
    Add a test that instantiates the server, calls each registered
    tool with an empty/valid payload, asserts the response shape is
    JSON-serialisable. Add a `igor-admin mcp list-tools` subcommand
    that dumps the current manifest so drift is visible. Scope:
    refactor + test scaffolding. Disposal: **DEFER** (not urgent;
    working). Ticket filed for when the MCP surface adds more tools.

### Gap 3 — No CC-session telemetry: no idea which skills are actually called how often

- Severity: **medium-low**
- Biomimicry: n/a
- Evidence: There is no counter, log, or aggregation of "skill
  invocations per session." Akien runs /sprint, /savestate, /ticket,
  /decided — but nobody's counting, so nobody knows whether any of
  the 19 skills is dead. Pass-1 gap.
- Proposed ticket:
  - id: `T-skill-telemetry`
  - title: Log every skill invocation to a skill_invocations table
  - size: S
  - tags: [CCWorkflow, Observability]
  - description: Add a UserPromptSubmit hook (or a Tool-call PostHook)
    that detects slash-command invocations and inserts a row into a
    new `skill_invocations(ts, skill, session_id, args_snippet)`
    Postgres table. After a month, produces a histogram — dead skills
    (0 invocations) are candidates for retirement, hot skills (100+)
    are candidates for further Haiku-ification or hook promotion.
    Disposal: **SHIP** (cheap, high-info).

### Gap 4 — CC has no way to verify its own MCP tools are alive before using them

- Severity: **low**
- Biomimicry: n/a
- Evidence: The `mcp__igor__*` tools silently fail if Igor isn't
  running. CC then fabricates plausible-looking output or retries.
  No pre-flight health check at session start.
- Proposed ticket:
  - id: `T-mcp-preflight`
  - title: context-load step N — MCP tool preflight (igor up? UC up? each tool reachable?)
  - size: S
  - tags: [CCWorkflow, Safety]
  - description: Add an explicit MCP preflight step to /context-load:
    ping each registered MCP server's list_tools, record which are up
    and which are stale. Report inline: "MCP: igor=up (20 tools),
    igor_akiendell=down (last seen 2h ago)". CC can then decide per-
    query whether to fall back. Disposal: **DEFER** — nice to have,
    not urgent; working.

### Gap 5 — Skill frontmatter inconsistency: some use `name:` and `description:`, some just `---`

- Severity: **low**
- Biomimicry: n/a
- Evidence: `/day-close/SKILL.md`, `/commit/SKILL.md` etc have
  frontmatter but no `model:` or `model_exception:` fields. No
  consistent schema.
- Proposed ticket:
  - id: `T-skill-frontmatter-schema`
  - title: Pin a SKILL.md frontmatter schema + a linter (bundled with day-close-audit)
  - size: S
  - tags: [CCWorkflow, Docs]
  - description: Define canonical fields: `name`, `description`,
    `model`, optional `model_exception`, optional `depends_on`
    (other skills), optional `cost_tier` (cheap|expensive). Add a
    check to `/day-close-audit` that parses each SKILL.md, validates
    frontmatter, and flags drift. Disposal: **SHIP** (trivial).

### Gap 6 — Igor-as-own-developer still blocked on cc_queue CLI surface

- Severity: **medium**
- Biomimicry: partial (the self-developer loop is a biomimetic claim
  about system-level self-improvement; the blocker is procedural).
- Evidence: Pass-1 11B identified this: "Igor's self-coding workflow
  seems to rely on the same queue that CC uses. A fully autonomous
  Igor would need his own internal work queue." Verified — Igor's
  self-edit + self-trainer loop calls `cc_queue.py` via subprocess,
  coupling Igor to CC's dev-loop infrastructure. This is OK for now
  (shared tooling is good), but the coupling means Igor cannot run
  without lab/claudecode being importable, and the emoji-grep hack
  means Igor's tools have to speak Unicode emoji.
- Proposed ticket:
  - id: `T-igor-internal-queue-abstraction`
  - title: Define an igor-internal queue interface that wraps but does not require cc_queue.py subprocess
  - size: M
  - tags: [CCWorkflow, IgorSelfDeveloper, Architecture]
  - description: After T-cc-admin-consolidation lands, Igor's self-
    edit + self-trainer tools call `lab.claudecode.api.ticket_add(...)`
    directly (Python import) instead of subprocess. This decouples
    Igor's self-developer path from the CLI layer. When eventually
    Igor needs his OWN queue (separate from CC's shared one), the
    interface swap is trivial — one line in Igor's tool. Scope:
    interface cleanup, no behaviour change initially. Disposal:
    **DEFER** — gated on T-cc-admin-consolidation.

---

## Dead-code cross-check

Habits referencing non-existent code in this area (CC-workflow
scripts): a spot check via `igor-admin habit list` equivalent isn't
run here (read-only audit); deferred to Pass 3 runtime verification.
Based on static grep:

- Habits referencing non-existent code in your area: **NEEDS_RUNTIME**
  — need a `habit_list` query cross-referenced with
  `lab/claudecode/*.py` function names. Request Pass 3 to run this.
- Code in your area not referenced by any habit or test (orphan
  candidates):
  - `lab/claudecode/slate_manager.py` — orphan (no skill reads it,
    only dead cc_skills/slateclose/SKILL.md references it)
  - `lab/claudecode/cc_skills/` — 27 SKILL.md files, entire
    subtree orphan
  - `lab/claudecode/cc_queue.py cmd_inject` — self-deprecated in docstring
  - `lab/claudecode/channel.py listen` mode — not invoked by any
    skill (CLI-ad-hoc only)
  - `lab/claudecode/reorder_slate_sections.py` — one-shot migration,
    appears to have run its course
  - Most of `lab/claudecode/migrate_*.py` (12 files) — one-shot
    migrations, all likely complete. Cross-check against palace
    `theigors/history` for which have run and can be archived.
  - Most of `lab/claudecode/seed_*.py` (65 files) — seed scripts
    that run once. Some are re-run after DB resets; audit which are
    load-bearing for the current database state vs. historical.

---

## What else?

### What else should we be asking?

- **Is the CC dev-loop itself biomimetic?** The sprint loop (ticket →
  claim → work → close) is a procedural pipeline. A biomimetic
  alternative: CC's "next action" should emerge from competition in a
  TWM-like workspace over { pending tickets, slate state, Akien's
  latest turn, cost/time budget }, rather than being dispatched by
  /sprint's hardcoded sequence. This is the same lesson we're trying
  to teach Igor. (Not urgent, but worth noting.)
- **Why do we have both `/day-close-audit` AND `/deep-audit`?** The
  first is a debris checklist, the second is an 11-persona parallel
  architecture review. Different cadences (daily vs weekly). But
  does the 11-persona parallel agent design scale beyond `/deep-audit`
  to other skills (e.g. `/review` with 5-6 personas)? Worth an
  experiment.
- **Should `/savestate` be automatic?** Every session-end has a high
  probability of needing it. A SessionEnd hook (T-cc-hook-autonomics)
  removes the "did I run /savestate?" cognition.

### What else might help Igor (and CC) learn and reason better?

- **Skill-invocation histograms** (T-skill-telemetry) tell us which
  skills are load-bearing vs decorative. After a month, retire zero-
  count skills — same pruning logic as dead habits.
- **Review-self-learning loop already exists** (`T-review-self-
  learning` gated, per `/review/SKILL.md`). Unblock it — once
  10-20 reviews are logged, the per-check confidence data is real.
- **Cross-session `lessons` memory**: when CC catches itself in a
  mistake twice in one session, that's a candidate rule for palace.
  Currently the user has to recognise the pattern and tell CC. A
  self-audit hook that grepped the session transcript for self-
  correction signatures ("wait, I should have...", "let me try
  again...") could surface candidates.

### What else can we optimize given small-hardware-research framing?

- **Skill model choices** (T-skill-model-audit-haiku) is the single
  biggest cost lever. Haiku-ifying 7 skills is potentially 60-70% CC-
  OR-meter reduction on those invocations.
- **Context-load rule-hash caching** (T-context-load-rule-hash)
  reduces per-session token burn by ~1500 when rules unchanged
  (which is most sessions).
- **Shared setup helper** (T-skill-shared-setup-helper) collapses
  venv activation + env vars + git pull into one hook call — a
  few hundred tokens saved per skill invocation.
- **Hooks replacing skills** (T-cc-hook-autonomics) — any skill that
  runs automatically every session is a candidate for hook demotion.
  Saves the tokens of skill-invocation ceremony.

### How do we perform the same review process of the database and its engrams?

Pass 1 proposed an `/audit-engrams` skill. CC-workflow integrator
view: this is the right shape, but it should reuse the `/deep-audit`
parallel-Haiku pattern rather than being a new skill shape. Specifically:

- `/deep-audit` already loads 11 parallel Haiku agents with
  per-panel lenses on CODE. A sibling `/deep-audit-engrams` (or a
  flag `/deep-audit --target engrams`) loads the same 11 personas
  but each panel reads ENGRAM rows instead of Python files. The
  Biomimicry-Engineer panel checks that each engram's biology-
  named cells actually do the named thing. The Linguist panel
  checks narrative clarity. The QA panel generates adversarial
  inputs per engram. Synthesis is unchanged.
- Output channel is unchanged: findings → cc_queue.
- This approach avoids proliferating skills and leverages existing
  infrastructure.

Proposed ticket (filed here since it's CC-workflow integrator
scope):

  - id: `T-deep-audit-engrams-variant`
  - title: /deep-audit --target engrams — reuse parallel-Haiku shape for engram review
  - size: M
  - tags: [CCWorkflow, Engrams, Audit]
  - description: Add a `--target` flag to `/deep-audit` accepting
    `code` (default) or `engrams`. In engrams mode, each panel's
    "files to read" list becomes a palace query for PROCEDURAL/
    INTERPRETIVE memory rows instead of filesystem paths. Panel
    lenses stay the same. Synthesis step stays the same. Scope:
    new flag + panel-prompt-template swap. Disposal: **DEFER** —
    blocked on T-deep-audit-engrams conceptual sign-off from Akien.

---

## Summary

- **Ticket candidates total:** 22 (16 in-area findings + 6 gaps;
  `T-deep-audit-engrams-variant` is additionally filed under the
  "what else?" engrams section)
- **Recommended SHIP:** 15
  - T-cc-admin-consolidation (L)
  - T-savestate-compact-one-shot (S)
  - T-retire-cc-skills-dir (S)
  - T-queue-api-no-json-echo (M)
  - T-context-load-rule-hash (S)
  - T-skill-model-audit-haiku (S)
  - T-skill-shared-setup-helper (S)
  - T-palace-echo-readme-only (S)
  - T-feedback-files-to-palace (S)
  - T-inertia-enforcement-from-palace (M)
  - T-cc-script-dead-code-sweep (S)
  - T-cleanup-queue-backup-artifacts (S)
  - T-cc-hook-autonomics (M)
  - T-cc-env-split-startup-check (S)
  - T-ticket-add-stdin (S)
  - T-savestate-atomic-flush (S)
  - T-skill-telemetry (S)
  - T-skill-frontmatter-schema (S)
  (count cross-checked: 18 SHIP when counting the gap tickets too)
- **Recommended DEFER:** 4
  - T-multi-slate-per-day (unclear if Akien needs it)
  - T-igor-mcp-modularize (working; not urgent)
  - T-mcp-preflight (nice-to-have)
  - T-igor-internal-queue-abstraction (gated on admin-consolidation)
  - T-deep-audit-engrams-variant (needs sign-off)
- **Recommended INVESTIGATE:** 0 — this area is action-ready.
- **Recommended DISCARD:** 0 — nothing fabricated or irrelevant.
- **Highest-stakes single finding:** **T-cc-admin-consolidation**.
  Collapses 9 scripts + 20 hardcoded DB URLs + 4 duplicate setup
  blocks + 1 silently-broken subprocess call into one module with
  one entry-point. Unblocks 4 other SHIP tickets that cleanly fold
  into it. This is the structural change that makes every other
  CC-workflow improvement small.
- **One sentence for Pass 3:** Verify with a runtime
  `mcp__igor__habit_list` query whether any habit's `code_ref`
  points at an orphan script in `lab/claudecode/` (the dead-skill-
  refs question), and confirm the `decision_manager.py:75` broken
  path really has been silently swallowed for weeks — if so, that's
  a leading example of the "exception-swallow hides real failures"
  pattern Pass-1 persona-1 flagged, but occurring in the dev-loop
  plumbing itself.
