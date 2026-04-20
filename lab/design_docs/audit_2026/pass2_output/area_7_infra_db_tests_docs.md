# Pass 2 deep-dive — INFRA + DATABASE + TESTS + DOCS

Auditor: Opus 4.7 (1M ctx), area 7 (renumbered from prompt's "area 8" — this is
the infra/db/tests/docs slice). Read the full Pass 1 report, the prompt
template, the shim `CLAUDE.md`, the canonical `db_proxy.py`, the raw-psycopg2
scripts (`cc_queue`, `decision_manager`, `palace_sync`, `session_manager`,
`slate_manager`, `docs_sync`, `github_sync`), `_PG_SCHEMA` + `_SCHEMA_MIGRATIONS`
in `cortex.py`, `tests/conftest.py`, `tests/test_three_schemas.py`,
`tests/test_d126_postgres.py`, `lab/docs/glossary.md`, and both
`lab/recovery_help_from_akien/CLAUDE*.md`.

---

## Per-finding verdicts

### Finding 1-silent-excepts — Silent exceptions & error swallowing
- Verdict: CONFIRMED_WORSE
- Blast radius: the "bare except" anti-pattern is SO pervasive in this area
  that `db_proxy.py` alone has fifteen `except Exception as _bare_e:` blocks
  whose sole behavior is `logging.getLogger(__name__).warning("bare except
  in wild_igor/igor/memory/db_proxy.py: %s", _bare_e)` — i.e. a self-labelled
  bug admission that was never fixed. Every connection close, every
  savepoint cleanup, every metric record has one. The warning lies — the
  path is `lab/utility_closet/db_proxy.py` (the file was moved during the
  rack refactor and the hard-coded warning string stayed stale). Pass 1
  listed four examples; the real count in core infra is closer to fifty.
  This matters because DB-connection failures, transaction rollback
  failures, and pool-return failures are exactly the errors you MUST not
  swallow — swallowing them leaks connections and corrupts the pool.
- Biomimicry: n/a (infra).
- Proposed ticket:
  - id: T-bare-except-purge-infra
  - title: Replace `_bare_e` warnings with real error handlers across db_proxy + sync scripts
  - size: M
  - tags: [infra, db, hygiene, reliability]
  - description: Every `except Exception as _bare_e: logging...warning("bare
    except in...")` in `lab/utility_closet/db_proxy.py`, `lab/claudecode/
    cc_queue.py`, `lab/claudecode/decision_manager.py`, `lab/claudecode/
    session_manager.py`, `lab/claudecode/slate_manager.py`, `lab/claudecode/
    docs_sync.py`, `lab/claudecode/palace_sync.py`, and `lab/claudecode/
    github_sync.py` is a debt marker left by an earlier audit that never
    got cleaned. Classify each site into three buckets: (a) safe to swallow
    with a structured log + metric increment (e.g. "close on a connection
    that's already closed is fine"); (b) must propagate or the caller will
    behave wrongly (e.g. "`self._pool.putconn()` failure means a leaked
    connection — must surface"); (c) instrumented-panic — something
    invariant-breaking happened, call `forensic_logger.log_error()` with a
    stable `kind=` tag so habits can fire on it. Fix the lie where the
    warning message names `wild_igor/igor/memory/db_proxy.py` but the code
    actually lives in `lab/utility_closet/db_proxy.py` (the shim is the
    other file). Scope boundary: do NOT delete the except clauses; replace
    them one at a time with classified behaviour. Do NOT touch HIGH-inertia
    exception handling in `cognition/reasoners/base.py`. Retire the
    auto-generated warning pattern in the audit checker that inserted
    these. Safe to ship incrementally; no old path to delete.
- Disposal: SHIP

### Finding 3-db_proxy-layer — Unnecessary db_proxy layer & SQL dialect leak
- Verdict: CONFIRMED_NARROWER — Pass 1 said "delete the entire proxy".
  That's too aggressive. The proxy DOES justify its existence in three
  ways: (i) ThreadedConnectionPool management; (ii) latency/slow-query
  metrics ring; (iii) search_path management on connection checkout (a
  real need, not a leak — see `_PGContext.__enter__`). What does NOT
  justify itself is the SQLite-compat shim: `_PGConnWrapper`,
  `_PGRowProxy`, `_translate_insert_or_replace`, `_INSTR_RE`,
  `executescript`, PRAGMA no-op, lastrowid via LASTVAL, and the blanket
  `?→%s` replace. That compatibility layer exists ONLY to smooth legacy
  SQLite-era call sites. Post-D126 the SQLite path is fallback-only (see
  `make_home_proxy`), and CLAUDE.md states "NO SQLITE ANYWHERE". So the
  *translation* layer is dead weight propping up a vestigial SQLite
  fallback, while the *proxy* layer has real value.
- Blast radius: every cortex query, every call site in `tools/`, every
  migration. Deleting `_PGConnWrapper` without a migration plan is fatal.
  HIGH-inertia touched: `wild_igor/igor/memory/cortex.py` reads `MEM_COLS`
  from this module, and `cortex._init_pg_schema` walks `_PG_SCHEMA`
  through `executescript`. The savepoint-on-every-DML pattern in
  `execute()` is also load-bearing — removing it breaks the `try:
  conn.execute(ALTER TABLE ADD COLUMN) except: pass` idiom in
  `_init_db`. Tests: `test_d126_postgres.py` pins executescript + PRAGMA
  no-op + PGConnWrapper contract. No habit `code_ref` points at
  `_PGConnWrapper`. Biomimicry: n/a.
- Proposed ticket:
  - id: T-db-proxy-sqlite-shim-retire
  - title: Retire db_proxy SQLite-compat translation layer; keep pool + metrics
  - size: L
  - tags: [infra, db, simplification, cleanup-D126-tail]
  - description: Cortex and every other live caller now run Postgres; the
    SQLite fallback in `make_home_proxy` is the dead branch. Retire the
    translation layer in three phases so no flag-day is needed. Phase A
    (audit): grep every callsite that uses SQLite-isms (`?` placeholder,
    `INSERT OR REPLACE`, `INSERT OR IGNORE`, `PRAGMA`, `INSTR`, raw
    `executescript`, `lastrowid`). Phase B (rewrite): convert each site
    to native Postgres (`%s`, `ON CONFLICT ... DO UPDATE`, `strpos`,
    split-and-execute-each-stmt locally). Phase C (delete): remove
    `_PGConnWrapper`, `_PGRowProxy`, `_translate_insert_or_replace`,
    `_INSERT_OR_IGNORE`, `_INSERT_OR_REPLACE`, `_INSTR_RE`,
    `_TABLE_PK`, `DatabaseProxy` (SQLite), `_DBContext`, `_in_explain`,
    `ensure_index` (SQLite variant), and the SQLite branches of the
    factory functions. What KEEPS: `PGDatabaseProxy` (pool + metrics +
    search_path + slow-query log + factory routing). What stays in
    `wild_igor/igor/memory/db_proxy.py` (the shim): one-line re-exports
    narrowed to the surviving symbols. Scope boundary: do NOT touch the
    `feedback_db_proxy_limitations.md` rule — that rule survives because
    the raw psycopg2 users must also obey "use jsonb_exists not ?". Old
    path is safe to delete after Phase B ships and tests stay green for
    one week. Touches HIGH-inertia `cortex.py` — Akien reads this ticket.
- Disposal: INVESTIGATE (needs a phase-A grep pass before sizing firms up)

### Finding 3-raw-psycopg2-bypass — Raw psycopg2 in cc_queue, decision_manager, palace_sync
- Verdict: CONFIRMED_WORSE — Pass 1 listed three files; actual count in
  `lab/claudecode/` is seven production scripts totalling ~2,998 lines,
  all opening their own psycopg2 connections, all duplicating the
  `_conn()` helper pattern, all bypassing the metrics ring, all ignoring
  slow-query thresholds, all re-implementing `IGOR_HOME_DB_URL ||
  IGOR_DB_URL` fallback logic. This is a parallel data-access surface
  with zero observability.
- Blast radius: `cc_queue.py` (960 lines), `session_manager.py` (500),
  `slate_manager.py` (429), `github_sync.py` (337), `decision_manager.py`
  (315), `docs_sync.py` (299), `palace_sync.py` (158). Every CC workflow
  ticket touches one of these. None of them obey CLAUDE.md's rule "All DB
  access through db_proxy, never raw psycopg2 in tools." That rule is
  demonstrably not enforced — the audit checker `audit_check_sqlite_
  imports.py` exists but there's no corresponding `audit_check_raw_
  psycopg2.py`. No habit `code_ref` depends on the `_conn()` helpers.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-lab-scripts-use-infra-proxy
  - title: Route `lab/claudecode/*` scripts through `make_infra_proxy()`
  - size: M
  - tags: [infra, db, rule-enforcement]
  - description: Every `_conn()` in `lab/claudecode/*.py` is a duplicate
    of every other `_conn()`. Replace each with `make_infra_proxy()` —
    this gives the CC tooling the same metrics/slow-query/search_path
    contract as Igor's live path, and lets the infra proxy own DSN
    fallback logic in ONE place. Scope boundary: do NOT change the CLI
    shape of any script — this is an internal refactor. After the first
    three files convert, add an audit checker
    `lab/claudecode/audit_check_raw_psycopg2.py` that flags new raw
    `psycopg2.connect` calls in `lab/claudecode/` and `wild_igor/igor/`
    and wire it into the pre-commit hook. Old `_conn()` helpers safe to
    delete per-file after their script converts. Pairs naturally with
    the sibling ticket T-lab-scripts-unify-into-cli (below) — if we
    consolidate these seven CLIs into one binary, the conversion work
    drops by ~40%.
- Disposal: SHIP

### Finding 3-n1-cc_queue-save — N+1 UPSERT in cc_queue._save
- Verdict: CONFIRMED. Line 117-151 of `cc_queue.py`: `for t in tasks:
  cur.execute(INSERT...)`. On a 200-ticket queue that's 200 round-trips
  per `_save()`. Every status change (claim, done, block, propose,
  approve, reset, ungate, set-decision, set-epic, set-worker,
  set-github-issue, needs-review, gate) calls `_save(tasks)` which
  re-upserts EVERY ticket, not just the changed one. So a one-field
  update = 200 upserts = one full table rewrite.
- Blast radius: this is the hottest write path in CC's workflow. Every
  /sprint start, /commit, /done passes through here. Latency scales
  linearly with queue size. The queue has only grown. No tests pin this
  behavior, so the fix is low-risk.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-cc-queue-upsert-only-dirty
  - title: cc_queue._save: upsert only dirty tickets, or switch to per-op UPDATE
  - size: S
  - tags: [infra, db, performance]
  - description: Replace the "rewrite every ticket on every change"
    pattern with one of two shapes — either (a) the `cmd_claim`/`done`/
    etc. helpers take a `dirty_ids` set and `_save` accepts `dirty_ids=
    None` to preserve the current full-rewrite semantic for batch
    imports, while `dirty_ids={tid}` writes just that one row; or (b)
    each cmd_ function becomes a targeted UPDATE statement and the full
    `_save` goes away. Shape (a) is smaller. Shape (b) is cleaner but
    touches more sites. Either way the queue echo (`queue.json`) still
    regenerates atomically from `_load()` after the change. Scope
    boundary: do NOT change the `INSERT ... ON CONFLICT` SQL (Postgres
    native is correct). Touches no HIGH-inertia code.
- Disposal: SHIP

### Finding 3-n1-book-learner — N+1 cortex.store in book_learner
- Verdict: CONFIRMED — deferred to area-6 (reading + book_learner) which
  owns `book_learner._deposit_nodes`. This area flags it but doesn't
  ticket it, to avoid double-counting.
- Disposal: DEFER (to area-6)

### Finding 3-listen-notify-triggers — Under-utilization of Postgres features
- Verdict: CONFIRMED. Zero occurrences of `LISTEN` or `NOTIFY` anywhere
  in `wild_igor/igor/`. The TWM-polling `push_sources` thread wakes every
  few seconds to check `twm_observations`. That's hundreds of no-op
  queries per minute in idle state.
- Blast radius: changing TWM publish to issue a `NOTIFY twm_insert` and
  adding ONE listener thread in Igor eliminates the polling storm. But
  the change touches HIGH-inertia territory (cortex.twm_push + the
  push_sources family). Materialized views for `get_hot_attractors` is a
  smaller, safer first step.
- Biomimicry: procedural-with-bio-name — "TWM is pushed; others scan"
  pretends to be a global workspace but the scan is pull-polling, not
  push-driven. The honest mechanism would be: a write to
  `twm_observations` fires a Postgres trigger that emits NOTIFY; ONE
  consumer thread in Igor does `cur.execute("LISTEN twm")` and blocks on
  `conn.notifies`. Then each subscriber (NE, basal_ganglia, response_
  coherence) would register a Python-side callback. This IS the "surface
  multiple connected things and let salience competition decide" pattern
  from CLAUDE.md persona — the current polling flattens it into a
  linear loop.
- Proposed ticket:
  - id: T-twm-listen-notify
  - title: TWM publish fires NOTIFY; push_sources block on LISTEN instead of polling
  - size: L
  - tags: [infra, db, performance, biomimicry, cognition-loop]
  - description: Three pieces. (1) Add a Postgres trigger on
    `instance.twm_observations` AFTER INSERT that calls
    `pg_notify('twm', row_to_json(NEW))`. (2) In
    `wild_igor/igor/cognition/push_sources.py`, replace the polling loop
    with a dedicated listener thread that holds a connection in
    `LISTEN twm` mode, reads `conn.notifies`, and fans out to
    subscribers via an in-process event bus (threading.Event + queue, or
    a small pub/sub class — no Redis needed for single-process Igor).
    (3) Keep polling as a degraded fallback if the listener dies; the
    daemon_supervisor should notice and restart the listener. Scope
    boundary: do NOT change the TWM table shape; do NOT change what
    observations are pushed; only change HOW subscribers get woken. This
    is the "biomimetic framing" — subscribers listen, they don't
    question-ask. Touches HIGH-inertia cortex.twm_push (must emit the
    NOTIFY if we use pg_notify from Python instead of a trigger; a
    trigger keeps cortex unchanged). Prefer the trigger shape for that
    reason. Ship the trigger in m060, the listener in a follow-up
    ticket. Safe to keep old polling for a week after listener ships,
    then retire.
- Disposal: INVESTIGATE — needs Akien's sign-off on listener thread
  lifecycle before shipping (interacts with daemon_supervisor).

### Finding 3-merge-candidates — Redundant tables: docs_entries, github_tickets, clan.memories-tickets
- Verdict: CONFIRMED. Three separate tables store "a document with
  status, title, body, type": `infra.docs_entries` (DSB-sourced decisions
  and gaps), `infra.github_tickets` (GH issues mirror), `clan.memories`
  with `parent_id='TICKETS_ROOT'` (CC's canonical tickets). A fourth
  partial: `infra.decisions` (used by `decision_manager.cmd_open/
  cmd_resolve`) overlaps with `docs_entries` rows where
  `entry_type='decision'`. The duplication exists because each got added
  in a different sprint without retiring the previous.
- Blast radius: every sync script reads/writes one or more of these
  tables. `decision_manager` writes to `docs_entries` AND a separate
  `decisions` table (see `cmd_resolve`). `github_sync.push-queue` copies
  from `clan.memories` tickets to `github_tickets`. Consolidation is
  possible but touches every sync script.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-documents-table-unify
  - title: Merge docs_entries, decisions, github_tickets, ticket-rows into one `infra.documents`
  - size: XL
  - tags: [infra, db, schema-simplification, strategic]
  - description: Collapse four overlapping tables into a single
    `infra.documents` row shape: `id | doc_type (decision|gap|ticket|
    github_issue) | source | title | body | status | metadata jsonb |
    created_at | updated_at`. `clan.memories` tickets rows are a
    narrower case — they're not just documents, they're graph nodes
    (they have parent_id, activation_count, etc.). PROPOSAL: keep the
    `clan.memories` row as the graph-participant, add a generated
    column or a view `infra.documents_v` that projects ticket rows +
    decisions + gaps + github_tickets into one read-side surface. That
    lets github_sync, docs_sync, decision_manager, cc_queue all query
    one view, while the write side keeps the strong-typed tables until
    we're ready to merge writes too. Scope boundary: this is a
    READ-side unification first. Write-side merge is a separate
    follow-up. Do NOT delete any of the four tables in this ticket —
    add the view, migrate queries, observe for two weeks, then ticket
    the table-drop. No HIGH-inertia. Old paths stay for observation
    window.
- Disposal: INVESTIGATE — needs Akien sign-off on strategic-level
  schema consolidation. Too big to ship unilaterally.

### Finding 3-memory_blobs-payload — memory_blobs overlaps with memories.payload
- Verdict: CONFIRMED. `memory_blobs.content` and `memories.payload`
  (JSONB from D260) are both "large/structured content attached to a
  memory". `memory_blobs` predates `payload`. Every live use case I
  checked could be served by `payload`. Tests don't block consolidation.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-memory-blobs-retire
  - title: Retire memory_blobs; lift content into memories.payload
  - size: M
  - tags: [infra, db, schema-simplification]
  - description: Audit every writer to `memory_blobs` (grep confirmed
    small set: blob_facia, scrub, blob_store). Draft a migration that
    copies `memory_blobs.content + tags + created_at` into
    `memories.payload.blob.{content,tags,created_at}` for each parent
    memory. Rewrite readers to prefer `payload.blob` and fall back to
    the old table. Ship the migration, let it run for a week, then
    DROP TABLE memory_blobs in a follow-up ticket. Scope boundary:
    do NOT touch `memory_embeddings` — that table legitimately lives
    apart for size reasons. HIGH-inertia `memory/models.py` is
    untouched; `payload` already exists there. Old table stays
    until observation window clears.
- Disposal: DEFER — correct direction, but no pain driving it now.

### Finding 3-sessions-slates-merge — Merge sessions + slates
- Verdict: REFUTED (mostly). They LOOK similar from outside but
  `sessions` is a work-session record (CC turn transcripts +
  decisions + key changes + next/in_flight) while `slates` is a daily
  work bundle (tickets list, name, done-when). Session is a
  time-series of CC conversation sessions; slate is today's work
  plan. They have different lifecycles (session.id = `2026-04-20a`;
  slate.id = `2026-04-20`; multiple sessions per slate). Merging
  would uglify both. The Pass 1 finding overstated the overlap.
- Biomimicry: n/a.
- Proposed ticket: (none — REFUTED, no work)
- Disposal: DISCARD — no ticket; Pass 1 got it wrong.

### Finding 3-schema-sketch — Redesigned schema
- Verdict: NEEDS_RUNTIME — Pass 1's clean-room schema is a sketch, not
  a testable claim. Most of its pieces are handled by the tickets above.
  One loose end: "merge ring_memory + twm_observations into
  instance_state with state_type column". That's plausible but risks
  scrambling two well-indexed hot tables for a label-clarity win. The
  shared lifecycle (both are instance-scoped, both have TTL/expiry,
  both are written on every turn) does argue for it.
- Proposed ticket:
  - id: T-instance-state-unify-investigate
  - title: Evaluate merging ring_memory + twm_observations into instance.instance_state
  - size: S (investigation, not code)
  - tags: [infra, db, schema, investigate]
  - description: Prototype on a test DB the shape `instance_state(id,
    state_type ring|twm, content, salience, urgency, expires_at,
    thread_id, metadata jsonb)` and measure query performance vs the
    current two-table shape. Deliverable: a decision doc saying
    `keep-split | merge | merge-but-partition`. Don't ship any schema
    change from this ticket — produce the decision only. Interacts
    with T-twm-listen-notify above (if that ships first, NOTIFY needs
    to fire on instance_state write with a filter on state_type).
- Disposal: INVESTIGATE

### Finding 4-db_proxy-race-mem-cache — _mem_cache unbounded
- Verdict: CONFIRMED. `Cortex._mem_cache: dict = {}` at line 839 has
  TTL eviction in `_cache_get` but no size cap. Long-running Igor (72h)
  will accumulate entries for every unique memory fetched at least
  once. Genesis types never expire. Non-genesis get TTL=300s expiry
  ONLY when `_cache_get` is called with that id again — if an id is
  fetched once and never again, it sits forever.
- Blast radius: memory growth is slow but monotonic. LRU policy is
  the standard fix; `functools.lru_cache` doesn't work because the
  TTL logic is custom. A plain OrderedDict + `maxsize=5000` wrap
  solves it.
- Biomimicry: n/a (implementation detail of the cache; the memory
  fetch itself is sound).
- Proposed ticket:
  - id: T-mem-cache-bounded-lru
  - title: Bound Cortex._mem_cache to LRU with size cap
  - size: S
  - tags: [infra, memory, long-run-stability]
  - description: Replace the plain dict in `Cortex.__init__` with an
    OrderedDict wrapper + `_MEM_CACHE_MAX = int(os.getenv('IGOR_MEM_
    CACHE_MAX', '5000'))`. On `_cache_put`, if over cap, pop oldest
    non-genesis entry first. Add a metric: `_mem_cache.len` exposed
    through `get_metrics()` or a new `cortex.cache_stats()`. Scope
    boundary: do NOT change genesis-immortal behavior. Touches
    HIGH-inertia `cortex.py` but the change is narrow and the class
    invariant stays intact. Pair with one test that inserts 6000
    entries and asserts cap holds.
- Disposal: SHIP

### Finding 4-training-corpus-race — _save_index race condition
- Verdict: CONFIRMED. `wild_igor/igor/cognition/training_corpus.py`
  line 89: `_save_index(index)` does `INDEX_FILE.write_text(...)` with
  no lock. 11 call sites, several from threads (fetch, _deposit_nodes,
  cron paths). Two threads racing on `fetch()` for different URLs =
  one's write overwrites the other's.
- Blast radius: a lost book registration means a book gets downloaded
  but never indexed — the corpus drifts from the index silently. Low
  frequency but not zero under the overnight reading load.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-training-corpus-index-lock
  - title: File-lock training_corpus index.json writes
  - size: S
  - tags: [infra, concurrency, reliability]
  - description: Wrap every `_save_index(index)` call with the same
    fcntl-based lock pattern `milieu.py` already uses. Since all 11
    call sites are in this module, the cleanest shape is: move the
    fcntl wrap INTO `_save_index`, so no caller has to remember to
    hold the lock; the read side in `_load_index` also acquires a
    shared lock so read-during-write doesn't return a half-written
    file. Scope boundary: do NOT touch fetch/extract logic. If
    Windows portability matters, use `filelock` library. Safe to
    ship; no old path to retire.
- Disposal: SHIP

### Finding 8-tier-gate-editable — Tier gating editable by self_edit
- Verdict: CONFIRMED — but cross-area; primary owner is area 7 (ops +
  milieu + scope_guard). This area flags the infra implication: the
  gate is an env-var read at process start, so a `.env` edit followed
  by `exit 42` loop restart flips the gate. Ticket belongs in area 7,
  not here.
- Disposal: DEFER (to area 7)

### Finding 10-silent-excepts-untested — Untested silent excepts
- Verdict: CONFIRMED — covered by T-bare-except-purge-infra above.
- Disposal: SHIP (via T-bare-except-purge-infra)

### Finding 10-db_proxy-translation-untested — SQL translation untested
- Verdict: CONFIRMED_WORSE. Grepped `_translate_insert_or_replace`,
  `_INSERT_OR_REPLACE`, `_INSERT_OR_IGNORE` across all of `tests/` —
  ZERO matches. The translation logic has NO unit tests. This is the
  SQL layer every Cortex write goes through. `test_d126_postgres.py`
  tests the executescript and PRAGMA shims but not the INSERT OR
  REPLACE translator.
- Blast radius: any bug in `_translate_insert_or_replace` (pk
  detection, composite PK handling, column extraction regex)
  corrupts data silently — the generated SQL runs, it just updates
  the wrong rows or skips updates it should make. The table PK map
  `_TABLE_PK` is manually maintained; a new table added without
  updating the dict defaults to PK='id' which may not be true.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-db-proxy-translation-unit-tests
  - title: Unit-test `_translate_insert_or_replace` + INSTR + IGNORE translators
  - size: S
  - tags: [tests, db, reliability]
  - description: Add `tests/test_db_proxy_translation.py` with cases
    for: simple PK (`memories`, id); composite PK (`lists`,
    (list_name,item_key,instance_id)); missing PK in map (assert
    default behavior is documented, not surprising); INSERT OR REPLACE
    with `?` placeholders inside VALUES; INSERT OR IGNORE with
    existing `ON CONFLICT` (should not double-append); INSTR embedded
    in a SELECT. These are pure-string tests — no DB needed. Assert
    the generated SQL character-by-character. NOTE: if
    T-db-proxy-sqlite-shim-retire ships first, this ticket becomes
    moot; gate this ticket on that one not shipping within 60 days.
- Disposal: DEFER — do after T-db-proxy-sqlite-shim-retire decision.

### Finding 10-time-sleep-flakiness — Test flakiness from time.sleep
- Verdict: CONFIRMED_NARROWER — Pass 1 implied it's pervasive; grep
  shows 8 tests use `time.sleep(` (out of 185). Still worth fixing
  but not a crisis.
- Blast radius: the 8 files are `test_pe_plan_filter_probe`,
  `test_reply_obligation_fork`, `test_persistent_relationships`,
  `test_experiment_scheduler`, `test_pr_accretion`, `test_log_timer`,
  `test_utility_closet_client`, `test_pr_load_as_primary_attractor`.
- Proposed ticket:
  - id: T-tests-kill-time-sleep
  - title: Replace time.sleep in 8 tests with Event/condition-based waits
  - size: S
  - tags: [tests, reliability, flakiness]
  - description: For each of the 8 files, identify what the sleep
    waits for (thread wake, TTL expiry, background tick). Replace
    with (a) `Event.wait(timeout=...)` for thread-sync cases, (b)
    monkey-patched clock for TTL-expiry cases (many tests already
    use `freezegun` pattern), (c) direct method call for "wait for
    background scanner" cases (call the scan method directly instead
    of waiting for its schedule). Scope boundary: do NOT touch
    production code; tests only. Per-file review because the right
    replacement differs. Safe to ship file-by-file.
- Disposal: SHIP

### Finding 10-fixtures-aged-db — Fixtures don't reflect aged DB
- Verdict: CONFIRMED. `conftest.py` creates a fresh temp inbox per
  session and stamps `IGOR_TEST_MODE=1` — great for isolation, but
  means NO test runs against a large, long-lived memory graph.
  Performance regressions on aged data are invisible.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-aged-db-fixture
  - title: Add `aged_db` pytest fixture — pre-populated 10k-memory graph
  - size: M
  - tags: [tests, performance, fixture]
  - description: Build a once-per-session fixture that materializes
    a Postgres test DB with ~10k memories, realistic tails, plausible
    TWM load, 50 habits, and a populated word_graph. Seed is
    deterministic. Slow tests that want "aged" state depend on it;
    fast tests don't. Mark fixture with `@pytest.fixture(scope=
    "session")` and gate its build behind an env var
    `IGOR_RUN_AGED_DB_TESTS=1` so default pytest stays quick. Add a
    handful of marked tests: `test_cortex_search_p95_under_100ms`,
    `test_ne_scan_completes_in_2s`, `test_hot_attractors_query_sane`.
    Scope boundary: do NOT displace existing unit-test fixtures.
    Old paths: none to retire.
- Disposal: DEFER — fixture first, then the tests that use it. Ship
  fixture; tickets for individual aged tests follow.

### Finding 10-sys-path-insert — sys.path.insert in tests
- Verdict: CONFIRMED. 152 tests contain `sys.path.insert`. This means
  test collection is cwd-dependent and susceptible to shadow-imports.
- Proposed ticket:
  - id: T-tests-pyproject-path
  - title: Kill sys.path.insert in tests — pytest rootdir via pyproject/conftest
  - size: M
  - tags: [tests, infra, hygiene]
  - description: Set pytest `rootdir` + `pythonpath` in
    `pyproject.toml` (or `pytest.ini` if there's one already) so every
    test can import `wild_igor.igor...` without manual path injection.
    Delete the 152 `sys.path.insert(0, str(Path(__file__).resolve().
    parent.parent))` lines via a mechanical sed pass. Verify
    `pytest tests/` still collects from any cwd. Scope boundary:
    tests only, no production code. Safe to ship.
- Disposal: SHIP

### Finding 10-env-var-dependence — Tests mutate real env vars
- Verdict: CONFIRMED. Multiple tests set env vars without
  `monkeypatch` or `patch.dict` — mutations leak between tests and
  depend on developer shell state.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-tests-use-monkeypatch
  - title: Replace `os.environ[x]=y` in tests with monkeypatch/patch.dict
  - size: M
  - tags: [tests, hygiene, isolation]
  - description: Grep tests for `os.environ[` assignments; convert
    each to pytest `monkeypatch.setenv` or `unittest.mock.patch.dict`.
    Add a conftest-level autouse fixture that snapshots env at test
    start and restores at teardown so mistakes are self-healing.
    Scope boundary: tests only. Pair with T-tests-pyproject-path;
    they overlap in mechanical-sweep shape.
- Disposal: SHIP

### Finding 10-self-testing-gaps — Igor self-testing gaps
- Verdict: CONFIRMED — cross-area. Primary owner should be area 7
  (ops) or area 1 (cognition). Infra flavor: need one internal test
  harness habit that runs a fast smoke suite against live Igor
  state. This is tickets owned by area 1/7.
- Disposal: DEFER

### Finding 11-narrative-drift — Three CLAUDE.md versions + palace echo
- Verdict: CONFIRMED_WORSE.
  - `/home/akien/TheIgors/CLAUDE.md` (just rewritten 2026-04-20 as
    80-line bootstrap shim pointing at palace).
  - `/home/akien/TheIgors/lab/recovery_help_from_akien/CLAUDE.md`
    (129-line FULL copy, still says `/audit` not `/day-close-audit`,
    references `brainstem/`, `memory/models.py`, `cognition/
    reasoners/base.py` HIGH inertia — content is broadly current but
    frozen).
  - `/home/akien/TheIgors/lab/recovery_help_from_akien/CLAUDE.older.md`
    (113-line SQLite-era artifact — three SQLite references).
  - `/home/akien/TheIgors/lab/theigors/` — palace repo echo (10 rule
    markdown files, synced from palace DB).
  - `/home/akien/.claude/projects/-home-akien-TheIgors/memory/
    MEMORY.md` — CC auto-memory, which ALSO says "NO SQLITE" and
    restates many of the same rules.

  So there are FIVE versions of the same rules (counting MEMORY.md
  and the palace itself). The bootstrap shim rewrite fixed the tip
  but left the body.

- Biomimicry: n/a (but meta-observation: Igor's rules should follow
  the same "code > palace > bootstrap shim" hierarchy from CLAUDE.md
  itself — anything with drift potential should be a view over the
  palace, not a parallel copy).
- Proposed ticket:
  - id: T-recovery-docs-consolidate
  - title: Retire CLAUDE.older.md; make recovery/CLAUDE.md a regenerated snapshot
  - size: S
  - tags: [docs, drift, cleanup]
  - description: Three moves. (1) DELETE
    `lab/recovery_help_from_akien/CLAUDE.older.md` — it's an
    SQLite-era artifact that actively misleads. Git history
    preserves it. (2) Replace
    `lab/recovery_help_from_akien/CLAUDE.md` with a one-command
    regeneration from the palace — `lab/claudecode/palace_sync.py
    --emit-recovery` writes a full snapshot by walking
    `theigors/rules/*` and stitching into one file. Commit the
    snapshot weekly via a cron or day-close step. (3) Add a header
    to the regenerated file: "This file is GENERATED FROM PALACE.
    Edit the palace, not this file." Scope boundary: do NOT touch
    the shim CLAUDE.md at repo root — that's the bootstrap and it
    STAYS hand-edited. Touches no HIGH-inertia. Old path
    (CLAUDE.older.md) safe to delete immediately.
- Disposal: SHIP

### Finding 11-palace-echo-fourth-source — lab/theigors/ as 4th source
- Verdict: CONFIRMED. `palace_sync.py` writes `lab/theigors/` from
  the palace DB. That's a DB→file direction, marked read-only in the
  script's output, but the FILES are committed to git. Someone could
  edit them and commit; if palace_sync runs next, the edit is
  silently overwritten. Not theoretical — it's a live sync loop.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-palace-echo-guard
  - title: Mark lab/theigors/ generated; add pre-commit check + CI guard
  - size: S
  - tags: [docs, infra, drift, generated-files]
  - description: Two pieces. (1) Add an autogenerated banner to EVERY
    palace echo file: "# GENERATED from memory_palace. Edits will be
    lost. Update via palace_write or the palace itself." (Already
    partially present but inconsistent.) (2) Add a pre-commit hook
    that runs `palace_sync.py --dry-run` and fails the commit if
    `lab/theigors/` has uncommitted-in-DB changes — forces the edit
    to go through the palace first. (3) Add a README note in
    `lab/theigors/README.md` repeating the same warning. Scope
    boundary: do NOT change the palace schema; do NOT change the
    sync direction. Safe to ship.
- Disposal: SHIP

### Finding 11-glossary-drift — glossary.md vs implementation
- Verdict: CONFIRMED_WORSE. `lab/docs/glossary.md` still says:
  - LTM: "The main `memories` SQLite table." — SQLite is dead.
  - "Word graph: SQLite-backed" — SQLite is dead.
  - "DB proxy: Wraps every SQLite call" — SQLite is dead.
  - "Live DB: `~/.TheIgors/Igor-wild-0001/wild-0001.db`" — path
    refers to old SQLite file; actual live DB is Postgres.
  - "Reactive habit has a `code_ref` field" — still current
  - "Inertia formula" — general description, no explicit formula
    to compare. Pass 1 claimed drift; I can't confirm a specific
    numeric drift without digging into `models.py`.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-glossary-de-sqlite
  - title: Scrub SQLite language from glossary.md; add palace cross-links
  - size: S
  - tags: [docs, drift]
  - description: Line-by-line edit of `lab/docs/glossary.md`: every
    "SQLite" → "Postgres" where the underlying truth is Postgres;
    the DB path `wild-0001.db` → `Igor-wild-0001 (Postgres DSN)`;
    db_proxy definition → rewrite. Add at end a link back to the
    palace (`SELECT path FROM memory_palace WHERE path LIKE
    'theigors/%'`) and a note: "if a term here contradicts the
    palace, the palace wins." Scope boundary: do NOT relocate the
    glossary to the palace (that's T-glossary-into-palace, a
    separate ticket). Just fix the drift. Safe to ship.
- Disposal: SHIP

### Finding 11-redundant-scripts-cli — Seven scripts → igor-admin CLI
- Verdict: CONFIRMED. The seven `lab/claudecode/*.py` scripts
  (cc_queue, decision_manager, session_manager, slate_manager,
  docs_sync, github_sync, palace_sync) are each a small CLI over
  Postgres. Total 2,998 lines. Each has its own `_conn()`, each has
  its own argparse or sys.argv loop, each has its own error idiom.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-lab-scripts-unify-into-cli
  - title: Consolidate cc_queue + decision_manager + session_manager + slate_manager + docs_sync + github_sync + palace_sync into `igor-admin` subcommands
  - size: L
  - tags: [infra, cli, simplification]
  - description: Use `click` or stdlib argparse subparsers. `igor-
    admin queue {list|add|done|...}`, `igor-admin decision {add|
    show|...}`, `igor-admin session {...}`, etc. Each subcommand
    lives in a module `lab/claudecode/admin/{queue,decision,...}.py`
    that imports a shared `lab/claudecode/admin/db.py` (wrapping
    `make_infra_proxy()` — pairs with T-lab-scripts-use-infra-proxy).
    Keep each script as a thin shim that calls the subcommand, so
    `python3 cc_queue.py list` still works during migration. After
    30 days of coexistence, delete the shims. Scope boundary: do
    NOT change semantics or DB shape; only the entrypoints. No
    HIGH-inertia. Safe incremental migration.
- Disposal: DEFER — pairs with T-lab-scripts-use-infra-proxy; ship
  the proxy routing first, then consolidate. Otherwise we do the
  same work twice.

---

## Pass 1 gaps (findings Pass 1 missed in this area)

### Gap 1 — SQLite fallback path contradicts "NO SQLITE ANYWHERE"
- Severity: high
- Biomimicry: n/a
- Evidence: `lab/utility_closet/db_proxy.py:848`
  ```python
  def make_home_proxy(db_path: Path = None):
      ...
      if db_url:
          return PGDatabaseProxy(...)
      ...
      return DatabaseProxy(db_path)   # SQLite — still reachable
  ```
  `CLAUDE.md` says "NO SQLITE ANYWHERE — everything Postgres." The
  SQLite code path is dead-with-a-pulse: if `IGOR_HOME_DB_URL` is
  unset, `make_home_proxy` returns a SQLite proxy. Every Igor boot
  has that env var set, so the branch never runs — but it exists,
  pulls in `import sqlite3`, carries ~400 lines of infrastructure,
  and forces the translation shim to survive.
- Proposed ticket:
  - id: T-sqlite-fallback-delete
  - title: Delete SQLite fallback branches from make_*_proxy factories
  - size: S
  - tags: [infra, db, dead-code, rule-enforcement]
  - description: Replace every SQLite-fallback return in
    `make_home_proxy`, `make_local_proxy`, `make_db_proxy` with a
    hard `raise RuntimeError("IGOR_HOME_DB_URL required — SQLite
    deprecated per CLAUDE.md")`. Bootstrap: if Igor needs to initialize
    a fresh Postgres DB, that's `psql -f` + `schema_runner`, not
    sqlite3. Retire `import sqlite3` from db_proxy.py; retire the
    `DatabaseProxy` class entirely. Gated by the same observation
    window as T-db-proxy-sqlite-shim-retire. SHIP after that one ships.
- Disposal: DEFER (pairs with T-db-proxy-sqlite-shim-retire)

### Gap 2 — `_bare_e` warning strings name the WRONG file
- Severity: medium
- Biomimicry: n/a
- Evidence: every `except Exception as _bare_e:` in
  `lab/utility_closet/db_proxy.py` logs `"bare except in
  wild_igor/igor/memory/db_proxy.py: %s"` — but that file is now a
  14-line re-export shim. Logs lie about file location. Confuses
  future audits (mine included — I had to grep to find the real file).
- Proposed ticket: covered by T-bare-except-purge-infra above.
- Disposal: rolled into T-bare-except-purge-infra

### Gap 3 — `_TABLE_PK` silently defaults to 'id' for unlisted tables
- Severity: medium
- Biomimicry: n/a
- Evidence: `lab/utility_closet/db_proxy.py:401-419`, then line 438:
  `pk = _TABLE_PK.get(table, "id")` — any new table whose PK isn't
  `id` breaks silently on INSERT OR REPLACE. The audit test
  `test_three_schemas` verifies migration names exist but not that
  `_TABLE_PK` is synchronized with the schema.
- Proposed ticket:
  - id: T-table-pk-registry-consistency-test
  - title: Test `_TABLE_PK` map matches actual table PKs
  - size: S
  - tags: [tests, db, invariant]
  - description: Add a test that introspects `information_schema.
    table_constraints` for all tables in the three schemas and
    asserts each row has an entry in `_TABLE_PK` with a matching
    value. Fails fast when a new migration adds a non-`id` table
    without updating the map. Scope boundary: test only. Moot if
    T-db-proxy-sqlite-shim-retire ships (no more `_TABLE_PK`).
- Disposal: DEFER — depends on translation-retire decision.

### Gap 4 — No `migrations/` directory; schema lives as Python list
- Severity: medium
- Biomimicry: n/a
- Evidence: `wild_igor/igor/memory/cortex.py:239` `_PG_SCHEMA` as a
  200-line Python triple-quoted string; `cortex.py:422`
  `_SCHEMA_MIGRATIONS: list[tuple[str, str]] = [...]` with 80+
  entries. There's no `migrations/` directory at the repo root. A
  migration is adding a Python tuple. Rollback is a code edit.
  Non-standard for a Postgres app; standard tooling (alembic, sqlx,
  golang-migrate) expects numbered SQL files.
- Proposed ticket:
  - id: T-migrations-to-sql-files
  - title: Migrate `_SCHEMA_MIGRATIONS` list to numbered SQL files under `migrations/`
  - size: L
  - tags: [infra, db, schema, tooling]
  - description: Create `migrations/` at repo root with files
    `0001_initial.sql`, `0002_add_arousal.sql`, ..., one per entry
    of `_SCHEMA_MIGRATIONS`. Schema runner walks the directory
    (alphabetical), checks `_migrations.name`, applies any missing.
    `_PG_SCHEMA` becomes `migrations/0000_bootstrap.sql`. Advantage:
    a migration becomes an SQL file a DBA can review, a GitHub PR
    can diff, and a human can run independently of Igor. Rollback
    patterns become possible. Scope boundary: do NOT change what
    each migration does, only where it lives. HIGH-inertia
    `cortex.py` is touched (trimmed), but only to remove the
    embedded SQL — no behavior change. Old path: the Python list
    remains for 30 days as fallback, then deletes.
- Disposal: INVESTIGATE — needs Akien's call on tooling stack
  (alembic vs homegrown).

### Gap 5 — Sprawling migrate_*_to_palace.py scripts
- Severity: low
- Biomimicry: n/a
- Evidence: 13 `migrate_*.py` scripts in `lab/claudecode/` — several
  are one-shot migrations already completed (migrate_rules_to_palace,
  migrate_decisions_to_palace, migrate_tickets_to_palace,
  migrate_skills_to_palace, migrate_slates_to_palace,
  migrate_sqlite_to_postgres, migrate_to_postgres,
  migrate_wg_to_postgres, migrate_wg_edges, migrate_emb1,
  migrate_lemmatize, migrate_node_ids, redis_migrate_wg). These are
  now execution artifacts — they ran, they worked, they sit in the
  live code tree.
- Proposed ticket:
  - id: T-migrate-scripts-to-archive
  - title: Move one-shot migrate_*.py scripts to lab/archive/migrations/
  - size: S
  - tags: [infra, cleanup]
  - description: Audit each `migrate_*.py`: if idempotent and still
    useful (covers forward-only schema change a box might need),
    fold into the new `migrations/` directory (Gap 4). If one-shot
    and already run on every live box, move to `lab/archive/
    migrations/YYYY-MM-DD_<name>.py` with a header comment "ran on
    <box> <date>, retained for forensic reference". Scope boundary:
    do NOT delete. Archive preserves history. After Gap 4 ships
    this becomes mostly mechanical.
- Disposal: DEFER (after Gap 4)

### Gap 6 — `closed_tickets.txt` as a sidecar file
- Severity: low
- Biomimicry: n/a
- Evidence: `cc_queue.py:166` `_prepend_closed_ticket` writes to
  `~/.TheIgors/lab/claudecode/closed_tickets.txt`. A flat file echo
  of closed tickets, outside both the palace and the canonical
  `clan.memories` store. Third sidecar: queue.json, log.jsonl,
  closed_tickets.txt.
- Proposed ticket:
  - id: T-closed-tickets-into-db
  - title: Drop closed_tickets.txt sidecar; derive from clan.memories status=done
  - size: S
  - tags: [infra, drift, cleanup]
  - description: The "closed tickets" list is fully recoverable with
    `SELECT id, metadata->>'title' FROM clan.memories WHERE parent_
    id='TICKETS_ROOT' AND metadata->>'status'='done' ORDER BY
    metadata->>'completed_at' DESC`. Delete the sidecar write in
    `_prepend_closed_ticket`. Add a `cc_queue.py closed [--limit N]`
    subcommand that queries the DB. If anything reads the sidecar
    (grep first), replace that read with the query. Scope: one
    file. Safe.
- Disposal: SHIP

### Gap 7 — Test count (185) with no coverage report
- Severity: medium
- Biomimicry: n/a
- Evidence: 185 test files exist. No `coverage.xml`, no
  `pytest-cov` config I could locate, no CI dashboard showing
  lines-covered-by-file. We don't know which parts of db_proxy,
  cortex._run_schema_migrations, or the sync scripts are actually
  exercised by any test.
- Proposed ticket:
  - id: T-coverage-baseline
  - title: Wire `pytest-cov` into pre-commit; post weekly coverage-by-file report
  - size: S
  - tags: [tests, ci, baseline]
  - description: Add `pytest-cov` to dev dependencies. `pyproject
    .toml`: `[tool.coverage.run] source = ["wild_igor", "lab/
    claudecode", "lab/utility_closet"]`. Add a day-close-audit step
    that greps the coverage report for <50% files in the infra area
    and files a ticket if new ones appear. Don't set a pass/fail
    threshold yet — just get visibility. Scope: CI/tooling only.
    Safe to ship.
- Disposal: SHIP

### Gap 8 — `_in_explain` thread-local reentrancy guard — unclear with pool
- Severity: low
- Biomimicry: n/a
- Evidence: `lab/utility_closet/db_proxy.py:34` `_in_explain =
  threading.local()` and the SQLite-side `_track_index_usage`
  check `_in_explain.active`. The flag is thread-local, but
  ThreadedConnectionPool may hand the same connection to different
  threads across time. The guard protects against RE-ENTRANT
  EXPLAIN-of-EXPLAIN (correct). But the Postgres path doesn't do
  EXPLAIN tracking at all (`ensure_index` is no-op on PG). So the
  complexity is only there for the SQLite-fallback branch that
  Gap 1 wants to delete.
- Proposed ticket: rolled into T-db-proxy-sqlite-shim-retire (index
  tracking is a SQLite-era feature that dies with the shim).
- Disposal: rolled in.

### Gap 9 — No smoke test for a fresh Postgres bootstrap
- Severity: high
- Biomimicry: n/a
- Evidence: `test_three_schemas.py` verifies the MIGRATION LIST is
  well-formed but it mocks `psycopg2.pool.ThreadedConnectionPool`
  so no SQL actually runs. No test creates an empty Postgres DB
  and runs the full `_PG_SCHEMA` + every migration to verify they
  apply cleanly in order. A malformed ALTER TABLE silently breaks
  every fresh-box boot.
- Proposed ticket:
  - id: T-fresh-pg-bootstrap-test
  - title: E2E test: fresh Postgres + full schema + migrations + smoke query
  - size: M
  - tags: [tests, db, ci, reliability]
  - description: Using `testcontainers-python` or a local
    docker-compose, spin up a fresh postgres:17, run `_PG_SCHEMA`
    + every `_SCHEMA_MIGRATIONS` entry, then issue one smoke query
    per schema (a SELECT on `clan.memories`, `instance.ring_memory`,
    `infra.sessions`). Assert zero errors. Gate behind
    `IGOR_RUN_PG_E2E=1` so devs without docker aren't blocked.
    Runs weekly in CI. Scope: tests only. Catches the one failure
    mode that currently has ZERO test coverage (fresh-box boot).
- Disposal: SHIP

### Gap 10 — Decisions live in TWO tables
- Severity: medium
- Biomimicry: n/a
- Evidence: `decision_manager.cmd_resolve` (line 242) UPDATES
  `decisions SET status=...` — implies a table `decisions`. But
  `cmd_add` upserts into `docs_entries`. So a decision lives in
  both `docs_entries` (as text row with entry_type='decision') AND
  `decisions` (as structured row with short_name/status/resolved_at).
  These can drift — `cmd_add` doesn't write to `decisions`;
  `cmd_resolve` only writes to `decisions`.
- Proposed ticket: rolled into T-documents-table-unify (Finding
  3-merge-candidates) — that's where this consolidation lives.
- Disposal: rolled in.

### Gap 11 — Rules content in TWO places: palace AND CLAUDE.md shim
- Severity: low (acknowledged by design)
- Biomimicry: n/a
- Evidence: `CLAUDE.md` (the new shim) correctly minimizes the
  bootstrap to the pre-DB destructive-action blocklist + a palace
  query. But if a rule in the shim contradicts the palace, which
  wins? The shim says "code > palace > CLAUDE.md > MEMORY.md" —
  so palace wins. Great. But the destructive-action blocklist IS
  duplicated in `theigors/rules/do-not.md` (palace) AND the shim.
  If they drift, the shim wins (because CC can't reach the DB to
  check).
- Proposed ticket:
  - id: T-shim-palace-consistency-check
  - title: Pre-commit hook: CLAUDE.md destructive-action blocklist matches palace do-not rule
  - size: S
  - tags: [docs, drift, pre-commit]
  - description: Hook that extracts the destructive-action blocklist
    from `CLAUDE.md` and diffs it against `theigors/rules/do-not`
    palace row. Fails commit if they differ. Accepts the shim being
    a SUBSET of palace (the shim is minimal by design) but not
    disjoint. Scope: hook only. Safe.
- Disposal: DEFER — minor.

### Gap 12 — `paths()` import inside db_proxy creates a circular-ish dependency
- Severity: low
- Biomimicry: n/a
- Evidence: `lab/utility_closet/db_proxy.py:32`
  `from wild_igor.igor.paths import paths` — the UC rack's db_proxy
  reaches INTO `wild_igor/igor/` for paths. This violates the
  `lab/` vs `wild_igor/` boundary that Pass 1's architecture
  persona flagged. `paths()` is used only to build `db_queries.log`
  location.
- Proposed ticket:
  - id: T-db-proxy-paths-decouple
  - title: Break db_proxy → wild_igor.igor.paths dependency
  - size: S
  - tags: [infra, boundaries, cleanup]
  - description: Either (a) accept `log_path=None` in PGDatabaseProxy
    constructor and default to `os.environ.get("IGOR_DB_LOG_PATH",
    "/tmp/igor_db_queries.log")`, OR (b) promote `paths.py` into
    `lab/utility_closet/paths.py` (it's a pure function, no
    runtime state, safe to move). Option (a) is smaller. Scope:
    one file + callers of `PGDatabaseProxy` (few). Safe.
- Disposal: DEFER — cleanup; no driving pain.

---

## Dead-code cross-check

- Habits referencing non-existent code in my area: need runtime
  grep of `habit.code_ref LIKE '%db_proxy%'` / `%cc_queue%` /
  `%decision_manager%` — skipping static confirmation since habit
  code_refs are stored in `clan.memories.metadata.code_ref`. The
  shape of the check: `SELECT id, metadata->>'code_ref' FROM
  clan.memories WHERE memory_type='PROCEDURAL' AND metadata->>
  'code_ref' ~ '(db_proxy|cc_queue|decision_manager|session_manager|
  slate_manager|docs_sync|github_sync|palace_sync)'` — then validate
  each hit still exists. This is Pass 3's runtime work per the
  template.
- Code in my area not referenced by any habit or test (orphan
  candidates):
  - `lab/claudecode/migrate_rules_to_palace.py`,
    `migrate_decisions_to_palace.py`,
    `migrate_tickets_to_palace.py`,
    `migrate_slates_to_palace.py`,
    `migrate_skills_to_palace.py` — one-shot migrations, already
    ran. Orphans by design; archive per Gap 5 ticket.
  - `lab/claudecode/redis_migrate_wg.py` — Redis migration;
    Redis was abandoned. Verify and archive.
  - `lab/claudecode/migrate_sqlite_to_postgres.py`,
    `migrate_to_postgres.py` — same D126 one-shots.
  - `lab/utility_closet/db_proxy.py::DatabaseProxy` class (SQLite)
    — live but unreached per Gap 1.
  - `lab/utility_closet/db_proxy.py::_PGConnWrapper.executescript`
    — reached, but only for legacy multi-statement SQL; half the
    call sites could use native PG multi-stmt.
  - `wild_igor/igor/memory/db_proxy.py` — 14-line re-export shim;
    keep as long as Pass 1 cleanup continues; delete after
    T-db-proxy-sqlite-shim-retire lands.

---

## How could we be using Claude Code better (standing remit)

This area's touchpoints with the dev loop:

1. **Skills don't exploit the UC rack architecture.** Every lab
   script (`/sprint`, `/commit`, `/decided`) shells out to
   `cc_queue.py`, `session_manager.py`, etc. Those scripts each
   open a Postgres connection. A CC session with 20 tool calls
   opens 20 connections. If T-lab-scripts-unify-into-cli ships
   AND the CLI becomes a long-lived local service (or talks to
   UC via a socket), connection churn drops 10x.

2. **No skill loads the palace-rules-hash and skips reload on
   match.** `/context-load` re-fetches rules every session. Pass 1
   persona 11 flagged this; the infra shape would be: add a
   `theigors/meta/rules_hash` palace row, `/context-load` reads
   ONLY that row first, compares to the cached hash in
   `~/.TheIgors/cc_channel/last_rules_hash`, and if match, skips
   the full rule reload. Saves ~2k tokens per session.

3. **Pre-commit hook opportunity: palace drift check.** If
   `CLAUDE.md` or `lab/theigors/*` files change in a commit, the
   hook should run `palace_sync.py --dry-run` to verify repo and
   DB are in sync before allowing the commit. Per Gap 11 and the
   palace echo finding.

4. **Audit-check script proliferation.** `audit_check_bare_
   except.py`, `audit_check_cortex_bypass.py`,
   `audit_check_hardcoded_instance.py`,
   `audit_check_igorbase.py`, `audit_check_sqlite_imports.py` —
   five separate files, one pattern each. A single `audit_lint.py
   --rule X` CLI with JSON rule definitions (already half there
   via `audit_checks.json`) would let CC run one command and
   get all rule violations at once, instead of skill-glue
   running five commands serially.

5. **The day-close-audit skill is the natural home for every
   "once per day" check this audit proposes.** Fresh-PG
   bootstrap smoke (Gap 9), coverage report (Gap 7), palace
   consistency (Gap 11), raw-psycopg2 grep (Finding
   3-raw-psycopg2). All one-liners, all cheap. Bundle them.

---

## What else (standing remit)

- **What should we be asking?** What's our test-to-production
  parity story? Tests mock psycopg2 almost everywhere, which means
  we test the call-shape but not the SQL. The fresh-PG E2E test
  (Gap 9) is a partial answer; the aged-DB fixture (Finding
  10-fixtures-aged-db) is another. Together they might catch 80%
  of DB-shape regressions pre-deploy.
- **Learning + reasoning:** the db_proxy's slow-query log is a
  rich training signal that's never consumed — 500-entry ring
  memory plus a persistent `db_queries.log` file, but no habit or
  module reads them. A "performance boredom" habit that fires
  when p95 crosses a threshold and proposes an index could be a
  self-improving loop.
- **Small-hardware optimization:** moving polling→LISTEN/NOTIFY
  (T-twm-listen-notify) is the biggest single idle-CPU win.
  Postgres generated columns for derived values (e.g. the
  "coalition size" in NE) push compute from Python to C. Both
  reduce laptop fan noise, which Akien will notice.
- **Reviewing the DB and its engrams:** the engram audit skill
  Pass 1 proposed (11-X) belongs in area 3 (habits + engrams),
  but this area owns the scaffolding for it — a view
  `infra.engram_audit_candidates` that surfaces low-activation
  high-age PROCEDURAL memories is a ten-line SQL change that
  gives the engram-audit skill a clean input. File as a small
  ticket in area 3, depending on this area's schema.

---

## Summary

- Ticket candidates total: 22 (15 from Pass 1 verification + 7 Pass 1 gaps that became tickets, minus 3 refuted/rolled-in)
- Recommended SHIP: 11
  - T-bare-except-purge-infra
  - T-lab-scripts-use-infra-proxy
  - T-cc-queue-upsert-only-dirty
  - T-mem-cache-bounded-lru
  - T-training-corpus-index-lock
  - T-tests-kill-time-sleep
  - T-tests-pyproject-path
  - T-tests-use-monkeypatch
  - T-recovery-docs-consolidate
  - T-palace-echo-guard
  - T-glossary-de-sqlite
  - T-closed-tickets-into-db
  - T-coverage-baseline
  - T-fresh-pg-bootstrap-test
  (14 items — corrected count)
- Recommended DEFER: 7
  - T-memory-blobs-retire (no driving pain)
  - T-db-proxy-translation-unit-tests (depends on shim-retire decision)
  - T-aged-db-fixture (ship fixture first, then dependent tests)
  - T-self-testing-gaps (cross-area, not primary here)
  - T-lab-scripts-unify-into-cli (after proxy routing)
  - T-sqlite-fallback-delete (pairs with shim-retire)
  - T-table-pk-registry-consistency-test (depends on shim decision)
  - T-migrate-scripts-to-archive (after migrations/ lands)
  - T-shim-palace-consistency-check (minor)
  - T-db-proxy-paths-decouple (minor)
- Recommended INVESTIGATE: 5
  - T-db-proxy-sqlite-shim-retire (L/XL, phase-A grep needed first)
  - T-twm-listen-notify (biomimetic change, needs Akien sign-off)
  - T-documents-table-unify (XL strategic merge)
  - T-instance-state-unify-investigate (is itself an investigation)
  - T-migrations-to-sql-files (tooling-stack decision)
- Recommended DISCARD: 1
  - T-sessions-slates-merge (Pass 1 got it wrong — REFUTED)

- **Highest-stakes single finding in this area:**
  `T-db-proxy-sqlite-shim-retire`. The SQLite-compat layer inside
  db_proxy is the load-bearing piece keeping 400 lines of dead
  translation code alive, and it's the foundation for the
  raw-psycopg2 bypass by lab scripts (they bypass the proxy
  partly because the proxy's API is weird — if the proxy spoke
  native PG, the bypass motive weakens). This single retire
  simplifies the DB layer, flushes out the SQLite fallback
  (Gap 1), obsoletes two test tickets, and reduces the
  attack surface for future SQL bugs.

- **Biggest deletion opportunity:** the SQLite-compat shim inside
  `lab/utility_closet/db_proxy.py` — ~400 lines of code,
  `_PGConnWrapper` + `_PGRowProxy` + the three translators +
  `DatabaseProxy` + `_DBContext` + `_in_explain` tracking + the
  SQLite fallback branches in the factories. With dependent
  deletes (SQLite fallback path, `_TABLE_PK` map, translator
  tests, archived migrate_sqlite*.py), realistic total deletion
  is ~700 lines. That's bigger than retiring any single sync
  script, bigger than any redundant-table merge's savings, and
  the most cleanly scoped.

- **One sentence for Pass 3:** decide whether
  `T-db-proxy-sqlite-shim-retire` ships this quarter — it's the
  cornerstone the other 11 infra tickets align behind, and
  deferring it leaves a dead-branch tax on every future DB
  change.
