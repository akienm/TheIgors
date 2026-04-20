# Pass 2 deep-dive — COMMS + UTILITY CLOSET + TOOLS + MCP

Scope: `lab/utility_closet/` (comms.py, rack.py, registry.py, budget.py,
filesystem.py, matter_shelf.py, machine_manager.py, db_proxy.py, agent_base.py,
failover.py, metrics_store.py, system_proxy.py, transports/\*), `wild_igor/igor/tools/registry.py`
(shim), `wild_igor/igor/tools/__init__.py` (tool self-registration surface),
`wild_igor/igor/tools/{budget,filesystem,channel_post,misfire_counter,discord,sudo_relay,or_model_refresh}.py`,
`lab/claudecode/utility_closet_server.py`, `lab/claudecode/igor_mcp.py`.

Out of scope here (routed to other areas): reading_tool / reading_engine
(area 6), pe_chain / habit compilation (area 3), cortex queries (area 2),
worker_foreman and goal_continuation (area 7), skill / slate / queue surface
(area 9). Cross-refs to those areas are called out where relevant.

## Per-finding verdicts

### Finding P1-1a — utility_closet_server fallback HTTP thread has no shutdown

- Verdict: `CONFIRMED`
- Evidence: `lab/claudecode/utility_closet_server.py:1098-1111`. When SSL is
  active, a second `uvicorn.Server` is constructed inside `_run_http()` and
  launched on a daemon thread with `asyncio.run(http_server.serve())`. No
  reference to `http_server` is kept; the shutdown handler at line 1049
  (`_shutdown`) only broadcasts and removes the PID file, then calls
  `sys.exit(0)`. The main uvicorn loop at line 1114 has a `finally:
  _remove_pid()` but no mechanism to cancel the fallback thread or drain its
  event loop.
- Blast radius: low per-boot (daemon threads die with the process), but on
  SIGTERM-driven shutdowns the fallback server never calls
  `http_server.should_exit = True`, so in-flight requests on the HTTP-only
  port are dropped abruptly. More importantly, the architecture forbids a
  graceful port-release ordering: if a restart happens fast enough, the new
  instance's bind on port+1 can race the OS socket teardown. Also: two
  separate Starlette `_make_app()` invocations means two independent
  `_comms` initializations (since `_init_comms` is the on_startup hook) —
  the HTTP-only app has its own `_comms` singleton distinct from the
  HTTPS app's. That silently bifurcates state (subscribers, channels) — any
  WebSocket client on the HTTP port sees a different comms universe.
- Biomimicry: n/a (pure infra).
- Proposed ticket:
  - id: T-uc-http-fallback-single-app
  - title: UC fallback HTTP server shares app state with HTTPS server
  - size: S
  - tags: [infra, comms, uc, correctness]
  - description: The SSL-active path in `utility_closet_server.main()` calls
    `_make_app()` twice (once for HTTPS on :8080, once for HTTP on :8082).
    Each invocation produces an independent Starlette app with its own
    `on_startup → _init_comms()` call, so the two servers hold separate
    `_comms` modules, `_session_clients`, `_session_history`, `_agents`
    dicts. Anything routed through the HTTP-only port is invisible to the
    HTTPS port and vice versa. The fix is to build ONE app and ONE comms
    module, then bind both listeners to it. Either (a) serve via a single
    uvicorn process on two ports using its multi-socket config, or
    (b) spin up two `uvicorn.Server` instances that share the same `app =
    _make_app()` object. Additionally, the background thread needs to
    receive the shutdown signal: keep a reference to the http_server and
    set `http_server.should_exit = True` in `_shutdown`. Scope excludes
    redesigning the SSL-vs-HTTP story — that's been stable. Files touched:
    `lab/claudecode/utility_closet_server.py` only. Safe to ship
    immediately once the dual-init is collapsed; no migration required.
  - disposal: SHIP

### Finding P1-1b — sudo_relay.py unused imports

- Verdict: `REFUTED`
- Evidence: `wild_igor/igor/tools/sudo_relay.py` imports `os` and uses
  `os.environ` at line 28 (RELAY_DIR default); imports `Path` and uses it
  at line 27. Pass 1's unused-import claim is wrong for this file. The
  underlying concern about lack of automated linting stands but is
  area-9's scope.
- Biomimicry: n/a.
- Proposed ticket: none (REFUTED; the linting remit goes to area 9).
  - disposal: DISCARD (refuted)

### Finding P1-2a — lab↔wild_igor boundary violation (comms transports reaching in)

- Verdict: `CONFIRMED_WORSE`
- Evidence: Pass 1 flagged `lab/claudecode/book_learner.py`'s sys.path
  insert into `wild_igor` (area 6). My area has the same disease, in a more
  load-bearing place:
  - `lab/utility_closet/transports/discord.py:54`
    `from wild_igor.igor.network.discord_bot import discord_bot`
  - `lab/utility_closet/transports/inference.py:96,106`
    `from wild_igor.igor.cognition.inference_gateway import get_gateway, make_context`
  - `lab/utility_closet/matter_shelf.py:209`
    `from wild_igor.igor.cognition.sensor_tree import create_sensor, ensure_sensor_root`
  - `lab/utility_closet/machine_manager.py:604`
    `from lab.utility_closet.system_proxy import ...` (ok) AND paths call at
    line 530 `from wild_igor.igor.paths import paths` — UC depends on an
    Igor-owned paths module.
  Meanwhile the inverse direction is papered over with re-export shims
  (`wild_igor/igor/tools/{budget,filesystem,registry}.py` → `lab/utility_closet/*`)
  per T-uc-*-shelf-inversion. The shims go in only one direction; UC
  *cannot import a shim pointing back* because that would loop. The result
  is asymmetric: lab depends on wild_igor at runtime, wild_igor's old
  imports are served by re-exports from lab. The "UC is a shared agent
  platform" story (D335) cannot hold while transports instantiate Igor
  subsystems directly.
- Blast radius: HIGH. Every transport that reaches into wild_igor breaks
  the "UC runs independently" promise from `utility_closet_server.py`'s
  docstring. matter_shelf and inference transport can't ship on a machine
  without a wild_igor checkout. Breaks the Windows agent story too
  (matter_shelf would need sensor_tree on a box that may never boot Igor).
  Also means the shelf-inversion tickets are only half done — the
  remaining half is "invert the dependency direction in transports and
  shelves too."
- Biomimicry: n/a (infrastructural layering, not biology).
- Proposed ticket:
  - id: T-uc-transport-dependency-inversion
  - title: UC transports and shelves stop importing wild_igor directly
  - size: L
  - tags: [infra, uc, layering, comms, transport]
  - description: The shelf-inversion work (T-uc-budget-shelf-invert,
    T-uc-filesystem-shelf-invert, T-uc-registry-move) moved canonical
    implementations from wild_igor/igor/tools/ to lab/utility_closet/ and
    left re-export shims on the wild_igor side. That work is structurally
    incomplete because UC-side code still reaches into wild_igor at three
    load-bearing sites: discord_bot (DiscordTransport), inference_gateway
    (InferenceTransport + OrChatTransport), and sensor_tree (MatterShelf).
    Proposed shape: define callback protocols on the UC side (e.g.
    `InferenceCallable = Callable[[str, str, dict], str]`,
    `DiscordSender = Callable[[int, str], bool]`,
    `SensorRegistrar = Callable[..., dict]`) and have the Igor side
    INJECT its implementations at boot, not the other way round. The
    transport constructors already accept optional params for
    config — add a function slot that defaults to None; UC comes up
    degraded if nothing injects. Files touched: `lab/utility_closet/transports/*.py`,
    `lab/utility_closet/matter_shelf.py`, `lab/utility_closet/machine_manager.py`
    (drop the wild_igor paths import), and a wiring file on the Igor side
    that pushes the callbacks in on startup (`wild_igor/igor/main.py` or a
    new `wild_igor/igor/uc_wiring.py`). Migration: keep the current
    imports as fallbacks behind a feature flag for one release, then
    remove. Old imports at transports/discord.py:54, transports/inference.py:96,
    matter_shelf.py:209, machine_manager.py:530 become injection points;
    the wild_igor imports themselves are NOT safe to delete until wiring
    exists. HIGH-inertia note: this touches no brainstem/ or
    memory/models.py files, but it does rewire the UC↔Igor boot order,
    which is load-bearing.
  - disposal: SHIP (after area 9 integrates with other layering work)

### Finding P1-4a — misfire_counter reads entire JSONL on every check

- Verdict: `CONFIRMED_WORSE`
- Evidence: `wild_igor/igor/tools/misfire_counter.py:153-181`. `_read_log`
  opens and line-by-line decodes the entire file on every call. Worse:
  `_increment_counter` (line 101-151) calls `_read_log` every time a
  single counter tick happens, so EACH tool error re-reads the whole log
  and then appends one line. N errors → N full re-reads, so cost grows
  O(N²). Combined with `get_active_counters` and `get_threshold_exceeded`
  also re-reading the log, any subsystem that queries misfires live pays
  the same price. Pass 1 said "progressively slower"; the actual pattern
  is quadratic.
- Blast radius: medium. Misfire counts feed into T-habit-repair-review;
  if the counter's own write path is slow, tools' own `registry.execute()`
  already pays that cost on every error (registry.py:162 catches, calls
  `_record_misfire` → `get_misfire_counter().record_tool_error` → full log
  read). With 131 tools and any error-cascade scenario, this becomes a
  dispatch-time bottleneck. No tests cover this — only
  `test_misfire_counter.py` exercises correctness, not scale.
- Biomimicry: n/a (observability infra), but the underlying notion
  ("repeated failure raises a flag") is a plausible analog of "allostatic
  load" — worth naming that way later.
- Proposed ticket:
  - id: T-misfire-counter-pg-backed
  - title: Move misfire_counter off JSONL onto Postgres with indexed queries
  - size: M
  - tags: [infra, observability, tools, perf]
  - description: Replace the JSONL log in `~/.TheIgors/logs/misfire_log.jsonl`
    with a Postgres table (e.g. `infra.tool_misfires(counter_key TEXT,
    attempted_name TEXT, dispatch_path TEXT, error_type TEXT,
    recorded_at TIMESTAMPTZ, metadata JSONB)`), indexed on
    `(counter_key, recorded_at)`. Counter increments become a single
    INSERT; threshold checks become a single SELECT COUNT with a window
    predicate; `get_active_counters` becomes a GROUP BY. This aligns with
    the "no SQLite / everything Postgres" rule and collapses the
    read-modify-write problem. Keep the same public API (`record_bash_exit`,
    `record_tool_error`, `get_threshold_exceeded`, `get_active_counters`,
    `reset_counter`) so callers don't change. Old JSONL file can be
    replayed once on migration then deleted. Files touched:
    `wild_igor/igor/tools/misfire_counter.py`, `wild_igor/igor/tools/registry.py`
    (no, callers don't need to change), a one-shot migration script in
    `lab/claudecode/migrations/`. Safe to delete the JSONL after the
    migration replays. No HIGH-inertia files touched.
  - disposal: SHIP

### Finding P1-4b — check_running noisy log level

- Verdict: `CONFIRMED_NARROWER`
- Evidence: `lab/claudecode/utility_closet_server.py:986` logs at DEBUG.
  Pass 1 said this should be WARNING. In context, each health-check URL
  attempt is one TCP round-trip — on a clean boot with no prior instance,
  the first two attempts to localhost:8080/health will fail (connection
  refused) before the server binds. DEBUG is correct for that case. The
  case Pass 1 cares about — "a failed health check leads to killing a
  stalled process" — is already logged at WARNING on line 989 ("Stalled
  utility closet...killing"). So the narrow version of the finding is
  correct (the per-URL failure could be INFO/WARNING if it's the last
  URL tried), but the blanket "this should be WARNING" is wrong.
- Blast radius: low. Log noise only.
- Biomimicry: n/a.
- Proposed ticket:
  - id: T-uc-check-running-last-url-warning
  - title: Elevate last-URL health-check failure from DEBUG to WARNING
  - size: S
  - tags: [observability, uc]
  - description: In `check_running()`, when ALL URLs in the probe list
    fail but the PID process is still alive, log the final URL's failure
    at WARNING (not DEBUG) alongside the existing "Stalled utility
    closet…killing" line. Per-URL intermediate failures stay DEBUG to
    avoid boot-time noise. Scope: only the final attempt. Files touched:
    `lab/claudecode/utility_closet_server.py:973-986`. One-line change.
  - disposal: DEFER (low value, wait for someone else to touch the file)

### Finding P1-11a — cc_queue.py as command-line script is brittle

- Verdict: `CONFIRMED` (area-9 scope, but affects my area through MCP)
- Blast radius: area-9 primary. My area connects via `request_compaction`
  in `igor_mcp.py:898` which uses tmux send-keys as fallback after file
  handoff; that path has the same "subprocess-invoked-as-CLI" smell.
- Biomimicry: n/a.
- Proposed ticket: (flag for area 9)
  - id: T-mcp-request-compaction-no-tmux
  - title: Eliminate tmux send-keys fallback in MCP request_compaction
  - size: S
  - tags: [mcp, cc-workflow, reliability]
  - description: `igor_mcp.py:_request_compaction` has three fallback
    paths: file handoff (preferred), direct file write, tmux send-keys.
    The tmux path is documented as "known to be unreliable mid-response"
    (line 926-927 in the current file). Proposal: delete the tmux path
    entirely. If the file write fails, return ERROR and let CC retry.
    The file-handoff hook (cc_hook_pending) is the design decision
    (T-compact-via-file-handoff) — the fallback contradicts that design.
    Scope: remove the tmux branch and the CLAUDE_TMUX_SESSION env lookup.
    Files touched: `lab/claudecode/igor_mcp.py:926-945` only.
  - disposal: SHIP (tiny, removes a known-brittle path)

### Finding P1-1c — tool naming inconsistency (_tool_audit_conversation_health)

- Verdict: `CONFIRMED`
- Evidence: `wild_igor/igor/tools/habit_health_audit.py:520` defines
  `_tool_audit_conversation_health`; the register call at line 554 uses
  `name="audit_conversation_health"`. The leading underscore on the
  Python symbol is a house-style marker for "internal — call through the
  registry," which is consistent across the codebase (see e.g.
  `wild_igor/igor/tools/metrics.py:260` `_get_tool_registry_report`
  registered as `get_tool_registry_report`). So this is a CONVENTION,
  not a bug. Pass 1 flagged it as inconsistent; looking at the ~260 tool
  register sites, the convention is "_prefix on the Python fn, no prefix
  on the tool name in the registry."
- Blast radius: none — the convention holds.
- Biomimicry: n/a.
- Proposed ticket: none — convention is consistent.
  - disposal: DISCARD (not a real finding)

### Finding P1-8a — habit misfire taxonomy is needed (trigger collision + stale action)

- Verdict: `CONFIRMED`
- Evidence: Current `misfire_counter.py` records three dimensions
  (`attempted_name`, `dispatch_path`, `error_type`) — it only captures
  "tool execution exception" and "bash 127 command-not-found". It does NOT
  capture (a) trigger collision (multiple habits match one input),
  (b) context mismatch (habit fires on keyword but broader context
  disagrees — see `response_coherence_inhibitor.py`), or (c) stale action
  (habit `code_ref` points at nonexistent code). Cross-check with DB:
  I ran a code_ref resolver against 116 unique habit code_refs; found
  `tools/operations.py:get_tool_registry_report` is stale (the symbol is
  in `tools/metrics.py` now, file renamed). At least that one stale
  code_ref exists in the live DB; the previous audit reported 58 dead
  refs (T-audit-2026-03-25) — cross-checking my area produced one
  confirmed stale plus three apparent-stale cases that turned out to be
  shim-masked imports (`tools.budget:get_budget_status`,
  `tools.or_model_refresh:refresh_or_models`, `tools.sudo_relay:sudo_relay_run`
  all resolve via the re-export shims or absolute imports).
- Blast radius: medium. Taxonomy is the training signal for
  self-improvement; without it, every misfire looks like an
  error-type line in a JSONL and the system has nothing to learn from.
  Trigger-collision misfires are invisible today.
- Biomimicry: HONEST when implemented — misfire tracking is a plausible
  analog of "error-related negativity" / prediction-error signaling. The
  current implementation is THIN (only catches exceptions), so it's
  better described as `procedural-with-bio-name` right now since
  "misfire" suggests more than it delivers. Honest version: record the
  expected outcome (was the habit expected to produce response text? a
  tool result? a TWM push?) and compare to the actual outcome — any
  divergence is a misfire, not just exceptions.
- Proposed ticket:
  - id: T-misfire-taxonomy-expand
  - title: Expand misfire taxonomy to cover trigger-collision and stale-action
  - size: M
  - tags: [observability, tools, habits, misfire, safety]
  - description: Extend `misfire_counter.py` (preferably paired with
    T-misfire-counter-pg-backed) so recorded misfires include a `kind`
    field with a defined enum: `EXCEPTION` (current default),
    `TRIGGER_COLLISION` (multiple habits matched one input, picked one
    by tiebreaker), `CONTEXT_MISMATCH` (habit fired but
    response_coherence_inhibitor vetoed), `STALE_ACTION` (habit
    code_ref does not resolve), `BARE_RESPONSE` (habit produced no
    output where one was expected). Wire the new kinds into the
    existing detection points: basal_ganglia at tie-break, response
    coherence inhibitor at veto, registry execute at ImportError,
    output_trainer where it already tracks bare responses. The three
    new kinds cover the biggest gaps from Pass 1 persona 8. Scope excludes
    redesigning the habit-repair UI — this is instrumentation only.
    Files touched: `wild_igor/igor/tools/misfire_counter.py`, one or
    two call-site files per kind. No HIGH-inertia edits.
  - disposal: DEFER (waits on T-misfire-counter-pg-backed)

### Finding P1-1d — shim duality for budget / filesystem / machine_manager / registry

- Verdict: `CONFIRMED`
- Evidence: Four files in `wild_igor/igor/tools/` (budget.py,
  filesystem.py, registry.py) and one `wild_igor/igor/cognition/machine_manager.py`
  exist only as re-export shims for lab/utility_closet canonical
  implementations. Each is 10-40 lines. Pattern is `from lab.utility_closet.X
  import *`. No wild_igor-side code remains.
- Blast radius: low as long as the shims exist; every import site still
  works. The real question is "when can these be deleted?" My grep found
  45+ remaining call sites that still import via the old paths (tools
  and other code). Deleting the shims now would break them; a week of
  grep-and-rewrite would finish the migration.
- Biomimicry: n/a (pure layering).
- Proposed ticket:
  - id: T-shim-sunset
  - title: Sunset wild_igor-side re-export shims (budget, filesystem, registry, machine_manager)
  - size: M
  - tags: [infra, cleanup, layering]
  - description: After T-uc-budget-shelf / T-uc-filesystem-shelf /
    T-uc-registry-move / T-uc-machine-manager-shelf landed, the wild_igor
    side of those modules became re-export shims. Task: sweep the codebase
    (tests, tools, cognition, docs) for imports of the old paths, rewrite
    to the new `lab.utility_closet.*` path, then delete the shim files.
    Do this in a single commit per shim so the delete is atomic with the
    last rewrite. Scope: DO NOT delete the shim before the last import
    is rewritten — that's a known footgun. No HIGH-inertia files. Files
    touched: `wild_igor/igor/tools/{budget,filesystem,registry}.py`,
    `wild_igor/igor/cognition/machine_manager.py`, plus ~45 import sites.
    Safe to delete old shims as the final commit step only.
  - disposal: DEFER (housekeeping; unblocks nothing urgent)

## Pass 1 gaps (findings Pass 1 missed in my area)

### Gap 1 — InferenceTransport passes invalid kwargs to make_context (dead on arrival)

- Severity: critical
- Biomimicry: n/a (bug).
- Evidence: `lab/utility_closet/transports/inference.py:110-113`:
  ```python
  ctx = make_context(
      purpose=purpose,
      metadata=metadata or {},
  )
  ```
  `make_context` at `wild_igor/igor/cognition/inference_gateway.py:1207`
  takes `(is_background, is_user_turn, research_mode, complexity)`.
  It does NOT accept `purpose` or `metadata`. Every call will TypeError.
  The caller catches the exception and returns a string
  `f"[inference-error] TypeError: unexpected keyword argument 'purpose'"`.
  That means InferenceTransport and OrChatTransport are broken but fail
  silently — the response "text" returned to the channel reads as an
  error banner, but no log alarm fires beyond `log.error` at line 117.
  Searches show no test coverage on this path (`tests/test_comms.py` uses
  MemoryTransport only; there is no `test_inference_transport.py`).
  Cross-ref to Area 1 (cognition + reasoning) — they own the
  make_context signature; this is the UC side failing to track their API.
- Proposed ticket:
  - id: T-inference-transport-make-context-signature
  - title: Fix InferenceTransport kwargs to match make_context signature
  - size: S
  - tags: [bug, comms, inference, transport, reliability]
  - description: The `purpose` and `metadata` kwargs passed to
    `make_context` at `lab/utility_closet/transports/inference.py:110-113`
    are not accepted by the function. Every `comms://model/*` request
    TypeErrors. Fix: use `make_context()` with supported args
    (`research_mode`, `complexity`) and carry `purpose` through to
    `gw.call(purpose_id=purpose, ...)` — which already takes it. Drop
    the `metadata` pass-through or move it to the gateway call's
    metadata param if one exists. Write a transport smoke test
    (`tests/test_inference_transport.py`) that monkeypatches the
    gateway and asserts a successful round-trip on
    `comms://model/default`. Also audit OrChatTransport which wraps
    InferenceTransport — same path is broken. HIGH-inertia note:
    inference_gateway itself is NOT modified; only the transport caller.
    Files touched: `lab/utility_closet/transports/inference.py`,
    possibly `lab/utility_closet/transports/or_chat.py`, new test file.
  - disposal: SHIP (critical — this transport is 100% broken)

### Gap 2 — ToolStats._samples keeps the slowest, not the newest

- Severity: high (statistical corruption)
- Biomimicry: n/a.
- Evidence: `lab/utility_closet/registry.py:89-95`:
  ```python
  def record(self, elapsed_ms: int, success: bool) -> None:
      self.call_count += 1
      if not success:
          self.error_count += 1
      bisect.insort(self._samples, elapsed_ms)
      if len(self._samples) > self._MAX_SAMPLES:
          self._samples.pop(0)  # drop oldest (smallest) when full
  ```
  The comment says "drop oldest" but `bisect.insort` keeps `_samples`
  sorted by VALUE, not time. `pop(0)` removes the smallest (fastest)
  latency. Over 1000+ calls with mixed fast and slow, the kept set skews
  toward slow — p50 and p95 both get biased high. The stats dict
  produced by `to_dict()` is used by `ops.py`'s tool-registry report
  (see `get_tool_registry_report` in `metrics.py:260`) which Akien
  looks at for tool health.
- Proposed ticket:
  - id: T-toolstats-sample-semantics-fix
  - title: ToolStats._samples should be newest-N, not sorted-N
  - size: S
  - tags: [bug, tools, stats, observability]
  - description: `ToolStats` uses `bisect.insort` to maintain sorted
    order, then evicts from index 0 when full — this drops the fastest
    call, not the oldest. Two viable fixes: (a) keep insertion-order
    list with fixed capacity (use `collections.deque(maxlen=1000)`) and
    sort only when computing percentiles, (b) keep the sorted
    representation but also remember insertion order in a ring buffer
    and remove the oldest value from both structures on eviction.
    Option (a) is simpler and what most stats libraries do. Percentile
    computation runs O(N log N) on every p50/p95 call — acceptable at
    N=1000 and called infrequently. Scope: single file, single method.
    Add a test that records 2000 samples of known distribution and
    asserts p50/p95 track the latest-1000 window, not the sorted-top-1000.
    Files touched: `lab/utility_closet/registry.py:79-124`,
    `tests/test_tool_registry.py`. No HIGH-inertia edits.
  - disposal: SHIP (quick, fixes a silent stat corruption)

### Gap 3 — Rack singleton exists but nothing ever registers with it

- Severity: medium
- Biomimicry: n/a.
- Evidence: `lab/utility_closet/rack.py:200-208` defines `get_rack()`
  singleton. `CommsModule` (comms.py) and `MatterShelf` (matter_shelf.py)
  inherit from `RackModule`. But grepping the entire codebase for
  `get_rack()` or `.register(` on a rack instance returns ZERO runtime
  callers — only tests (`tests/test_rack.py`, `tests/test_matter_shelf.py`).
  `utility_closet_server.py` initializes a `_comms` module directly; it
  never puts `_comms` on the rack. So the rack pattern exists
  structurally (inheritance chain, tests) but has no live shelf to
  stand on. This is "decorative architecture" — it looks like the system
  has a rack-based shelf pattern, but the real wiring is direct globals.
- Proposed ticket:
  - id: T-rack-wire-or-retire
  - title: Decide rack's fate: wire CommsModule + MatterShelf in or retire Rack
  - size: M
  - tags: [architecture, uc, rack, decision-needed]
  - description: `Rack`, `RackModule`, `get_rack()`, and the health-aggregation
    surface at `rack.py:152-177` are load-bearing IN DESIGN ONLY. Nothing
    runtime-registers with the rack. The fork: (a) WIRE IT — have
    `utility_closet_server._init_comms` call `get_rack().register(_comms)`
    and add the same hook for MatterShelf, Matter future shelves, Machine
    Manager as a shelf, Budget as a shelf; expose `/api/rack/health`
    that returns `get_rack().health()`. (b) RETIRE IT — delete
    `rack.py`, `matter_shelf.py`'s rack inheritance (keep the class,
    drop the RackModule base), keep the existing direct-global pattern.
    Option (a) pays for itself only if there's a second shelf that
    benefits from uniform health and lifecycle. My read: GH-185
    (matter_shelf) and GH-281 (SensorTree) and future discord_shelf are
    lined up to add shelves, so (a) is the right call. Scope: wire
    comms and matter; add /api/rack/health; update the fallback HTML
    dashboard to show rack module health. Files touched:
    `lab/claudecode/utility_closet_server.py`, `lab/utility_closet/rack.py`
    (if /api/rack/health needs a new helper), minimal matter_shelf.py
    adjustments. No HIGH-inertia edits.
  - disposal: INVESTIGATE (Akien call on wire-vs-retire — leaning wire)

### Gap 4 — show_timestamp Channel flag is silently ignored by the UC server

- Severity: medium
- Biomimicry: n/a.
- Evidence: `lab/utility_closet/comms.py:232` defines
  `show_timestamp: bool = True` on `Channel`. The docstring at
  comms.py:65-67 says "web UI renders HHMMSS prefix on author labels"
  and comms.py:131 says "edit utility_closet_server.py addMsg(), not
  this file" to change the format. But `utility_closet_server.py`'s
  fallback HTML (the served page) at line 1373-1383 unconditionally
  renders the `hhmmss` prefix whenever the `ts` field is present —
  never consults `show_timestamp`. The flag lives in the Python data
  model and in the tests (`tests/test_comms.py:87-91`) but is unused in
  the actually-served HTML. Ticket T-web-chat-timestamp-prefix
  (2026-04-20) is listed in comms.py provenance as delivered, but only
  the data side landed; the UI side doesn't honor it.
- Proposed ticket:
  - id: T-web-chat-timestamp-prefix-uses-flag
  - title: Actually respect Channel.show_timestamp in the UC web UI
  - size: S
  - tags: [ui, comms, bug, uc]
  - description: The `show_timestamp` flag added to `Channel` for
    T-web-chat-timestamp-prefix is stored but never consulted by
    `utility_closet_server.py`'s rendered HTML. Fix: thread the flag
    from the comms channel registry to the client (either via
    `/api/comms/channels` which already returns channel dicts — currently
    missing show_timestamp in the JSON — plus consulting it in the
    `addMsg` JS function, or server-side by not attaching `ts` on
    broadcast when the channel is `show_timestamp=False`). Favor the
    client-side approach: keep the data fully faithful and let the UI
    decide what to render. Scope: add `show_timestamp` to the
    `/api/comms/channels` response; store it in `channelMsgs`
    metadata; in `addMsg`, suppress the ts span if the current channel
    says so. Files touched: `lab/claudecode/utility_closet_server.py`
    only. Dist-built Svelte UI is untouched here because the fallback
    HTML is what's actually served when wild_igor/web_ui/dist is
    missing — ship this for the fallback first, then mirror in Svelte
    later.
  - disposal: SHIP (small, follow-through on already-filed ticket)

### Gap 5 — CC_SEND_URL hardcoded in igor_mcp.py breaks cross-machine MCP

- Severity: medium
- Biomimicry: n/a.
- Evidence: `lab/claudecode/igor_mcp.py:48`
  `CC_SEND_URL = os.environ.get("CC_SEND_URL", "http://localhost:8082/api/cc_send")`.
  The fallback assumes UC is on localhost. Per-machine MCP variants
  (`mcp__igor_akiendell__*`, `mcp__igor_yoga9i__*`, `mcp__igor_yogai7__*`)
  from CLAUDE.md all share this one module — if they run against different
  hosts, the fallback quietly routes to localhost. Every per-machine
  client needs `CC_SEND_URL` set explicitly or calls go to the wrong box.
  There's no per-host variant of `igor_mcp.py`.
- Proposed ticket:
  - id: T-mcp-per-host-routing
  - title: MCP cc/channel_send must resolve target host from machine registry
  - size: M
  - tags: [mcp, comms, cc-workflow, infra]
  - description: `igor_mcp.py` hardcodes CC_SEND_URL; per-machine MCP
    variants (`igor_akiendell`, `igor_yoga9i`, `igor_yogai7`) share the
    same module and need a way to route channel_send to the correct UC
    instance. Proposal: add a `MACHINE_ID` env var per MCP variant
    launch script; `_channel_send` looks up the UC URL via
    `machine_manager.get_machine(MACHINE_ID).uc_url`. Requires the
    machines table grow a `uc_url` column (or derive from ip + port).
    Fallback: existing localhost behavior preserves single-machine setup.
    Scope: igor_mcp.py routing, one column add to the machines table
    in infra.machines. Migration: write a one-shot script that backfills
    uc_url for the three known machines. Files touched:
    `lab/claudecode/igor_mcp.py`, `lab/utility_closet/machine_manager.py`,
    migration SQL. No HIGH-inertia.
  - disposal: INVESTIGATE (confirm this is actually broken in practice —
    Akien may be setting CC_SEND_URL in each launcher already)

### Gap 6 — DiscordTransport calls deprecated asyncio.get_event_loop() and has dead webhook path

- Severity: low
- Biomimicry: n/a.
- Evidence: `lab/utility_closet/transports/discord.py:96-105`:
  ```python
  def _send_webhook(self, bot, message: ChannelMessage) -> bool:
      try:
          if hasattr(bot, "_send_via_webhook"):
              import asyncio
              loop = asyncio.get_event_loop()
              if loop.is_running():
                  bot.send(0, message.payload)
                  return True
          return False
      except Exception:
          return False
  ```
  Three issues: (a) `asyncio.get_event_loop()` emits a DeprecationWarning
  in 3.10+ and fails in 3.12 when no loop is running; (b) the branch's
  conclusion ("queue it") ignores the channel_id (passes 0 to bot.send);
  (c) the `return False` path fires when the hasattr check fails OR
  when the loop isn't running — a silent no-op. The webhook path is
  effectively dead: the only success path (line 101) sends to channel 0.
  Grep confirms no caller relies on the webhook branch working.
- Proposed ticket:
  - id: T-discord-transport-webhook-remove
  - title: Remove dead webhook branch in DiscordTransport or implement it properly
  - size: S
  - tags: [comms, discord, cleanup]
  - description: `DiscordTransport._send_webhook` in
    `lab/utility_closet/transports/discord.py` is non-functional — it
    passes channel_id=0 on success, uses deprecated
    `asyncio.get_event_loop()`, and returns False silently in most paths.
    Option A: delete the branch and return False directly when
    `_extract_channel_id` fails and the address looks like a webhook;
    log a warning so the caller knows. Option B: implement real webhook
    send using `aiohttp` against the Discord webhook URL (needs webhook
    URL storage — would be a channel metadata field). Recommend A — the
    feature isn't used and the complexity isn't warranted until it is.
    Files touched: `lab/utility_closet/transports/discord.py:92-105` only.
  - disposal: SHIP (trivial cleanup)

### Gap 7 — machine_manager raises RuntimeError at import time if env var missing

- Severity: high
- Biomimicry: n/a.
- Evidence: `lab/utility_closet/machine_manager.py:34-39`:
  ```python
  _DB_URL = os.getenv("IGOR_HOME_DB_URL", "")
  if not _DB_URL:
      raise RuntimeError(
          "IGOR_HOME_DB_URL not set — machine_manager requires a Postgres connection. "
          "Set this env var at system level (not user level on Windows)."
      )
  ```
  This is module-load-time, NOT connect-time. Any import chain that
  reaches machine_manager without IGOR_HOME_DB_URL set dies immediately
  with an unrecoverable RuntimeError. I hit this trying to exec
  `from wild_igor.igor.tools import budget` during audit (because
  budget re-exports pull in machine_manager via some indirection).
  This makes the module un-test-runnable in clean CI environments and
  blocks static analysis tools. The fix is to defer the guard to first
  connection attempt; callers that need the URL can check it explicitly.
- Proposed ticket:
  - id: T-machine-manager-lazy-db-url-check
  - title: Defer machine_manager IGOR_HOME_DB_URL check from import to first call
  - size: S
  - tags: [bug, infra, uc, testability]
  - description: `lab/utility_closet/machine_manager.py` raises
    RuntimeError at module load if IGOR_HOME_DB_URL is unset. This
    breaks static imports in test/CI/audit environments and blocks
    any read of the module without a live DB. Move the check into
    `_pg_connect()` (first use) so the error fires only when someone
    actually touches the DB. Test that imports still work with the env
    var unset. Files touched: `lab/utility_closet/machine_manager.py:34-39`
    only. No behavior change for live runs.
  - disposal: SHIP (quick, unblocks tests and auditing)

### Gap 8 — comms.send() race between lock release and channel.last_active update

- Severity: low
- Biomimicry: n/a.
- Evidence: `lab/utility_closet/comms.py:337-355`. Lock held lines 337-348,
  released before line 351 ("Inherit retention…") and line 355
  ("channel.last_active = message.timestamp"). The `channel` reference is
  used after the lock is released. If a concurrent caller calls
  `register_channel` with the same address in between, two threads could
  race on `channel.last_active` writes. Probability low (Channel is a
  dataclass, write is a single assignment, Python guarantees atomicity
  for simple attribute writes). Still technically a read/write race on
  mutable dataclass state. Pass 1 persona 4 flagged similar patterns
  elsewhere.
- Proposed ticket: none (below-the-fold; left as a note for Pass 3)
  - disposal: DISCARD (cost to fix > cost of the race)

### Gap 9 — channel_append in utility_closet_server duplicates PostgresTransport work

- Severity: medium
- Biomimicry: n/a.
- Evidence: `utility_closet_server.py:269-298` directly writes to
  `channel_messages` via a raw psycopg2 connect-per-write pattern.
  Meanwhile `lab/utility_closet/transports/postgres.py` has
  `PostgresTransport.send` doing the same thing through a pooled
  connection. If _init_comms wires Postgres as the default transport
  (line 181-184), then every `_api_cc_send` call DOUBLE-WRITES: once via
  `_channel_append` (raw psycopg2) and once via the comms module flowing
  through PostgresTransport. The raw write path ignores the comms
  envelope, so duplicate rows differ (no message id, no retention, no
  content_type). Current `_api_cc_send` only calls `_channel_append`,
  not `_comms.send()`, so in production the double-write isn't happening
  YET — but `_channel_append` is the long-standing path and `_comms` was
  added more recently. The code is one glue call away from doubling.
- Proposed ticket:
  - id: T-uc-channel-append-via-comms
  - title: UC /api/cc_send routes through comms.send(), not direct psycopg2
  - size: M
  - tags: [uc, comms, layering, correctness]
  - description: `utility_closet_server._channel_append` maintains a
    parallel write path to `channel_messages` via raw psycopg2 alongside
    the CommsModule + PostgresTransport path. This is the exact
    architectural duality Pass 1 persona 2 flagged at the codebase
    level, in miniature. Proposal: have `/api/cc_send` (line 402),
    WebSocket `_receive` message handler (line 787-810), and
    `agent_send` (line 333-344) all call `_comms.send(ChannelMessage(...))`
    instead of `_channel_append`. Delete `_channel_append` once all
    three call sites are migrated. `_CHANNEL_FILE` (the
    messages.jsonl fallback) becomes dead code too — ticket it
    separately or fold it in here. The comms module already logs to a
    per-channel file when configured, so JSONL behavior is preserved via
    `log_base_dir`. HIGH-inertia note: none (UC server is MEDIUM
    inertia; this is refactor, not brainstem). Files touched:
    `lab/claudecode/utility_closet_server.py` only. Deletions safe once
    verified on a non-primary machine first.
  - disposal: SHIP (important for layering hygiene)

### Gap 10 — MCP audit_conversation_health does sys.path.insert into wild_igor

- Severity: low
- Biomimicry: n/a.
- Evidence: `lab/claudecode/igor_mcp.py:952-956`:
  ```python
  def _audit_conversation_health(hours: int = 24) -> str:
      import sys
      sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wild_igor"))
      from igor.tools.habit_health_audit import audit_conversation_health, format_report
  ```
  This is the lab→wild_igor boundary violation Pass 1 flagged for
  book_learner, in another form. MCP server reaches into Igor's tools
  package. Less bad than book_learner (it's called lazily, not at
  module load), but it shares the same code smell.
- Proposed ticket: piggyback on T-uc-transport-dependency-inversion.
  Flag only — the fix shape is the same as Gap 3 of that ticket.
  - disposal: DEFER (rolled into T-uc-transport-dependency-inversion)

## Dead-code cross-check

- Habits referencing non-existent code in my area:
  - `tools/operations.py:get_tool_registry_report` — stale code_ref.
    Actual location is `wild_igor/igor/tools/metrics.py:260`
    (`_get_tool_registry_report`, registered name `get_tool_registry_report`).
    The habit row(s) pointing at `operations.py` will miss on hot-reload
    resolution. Confirmed via DB query against
    `Igor-wild-0001`.
  - All other code_refs in my area resolve correctly via the re-export
    shims (budget → lab.utility_closet.budget; filesystem → ditto;
    sudo_relay stays in wild_igor; or_model_refresh stays in wild_igor).
- Code in my area not referenced by any habit or test (orphan
  candidates):
  - `lab/utility_closet/rack.py` — covered by tests/test_rack.py but no
    runtime callers (see Gap 3). Not technically orphan, but
    "architecturally dormant."
  - `lab/utility_closet/matter_shelf.py` — same story; tests exist, no
    runtime registration. GH-185 is the ticket for turning it on.
  - `lab/utility_closet/transports/or_chat.py` — tests exist at a
    smoke level but the broken InferenceTransport parent means nothing
    real uses this today. Listed as "broken transitively" not orphan.
  - `lab/utility_closet/failover.py`, `lab/utility_closet/metrics_store.py`
    — I did not audit the calling surface for these; flagging as
    potential orphans for Pass 3 to confirm against area 8 (infra + db).

## How could we be using Claude Code better (area-specific touchpoints)

- The `/day-close-audit` skill should query the habit code_ref resolver
  I used in this audit (simple importlib probe against `tools.X:fn`
  patterns) and flag stale refs every day. Current debris check doesn't
  catch stale code_refs. This is the ONE cross-check that prevents the
  58-dead-code_refs number from recurring.
- `/ticket` and `/decided` should reject filing against files in
  `wild_igor/igor/tools/{budget,filesystem,registry}.py` because those
  are re-export shims — any ticket that names them is probably aimed at
  the canonical `lab.utility_closet.*` file instead. A simple lookup
  table in `/review` would save misrouted tickets.
- The `mcp__igor__channel_send` + `mcp__igor__channel_read` round-trip is
  the single most useful CC-to-Igor surface. The fact that CC_SEND_URL
  has a localhost fallback (Gap 5) means `/readigor` accidentally works
  on single-machine setups and silently fails on remote ones. A
  `--host` flag on `/readigor` threading through to MCP wouldn't hurt.
- The shim-masked import resolution in my audit (e.g.
  `tools.budget:get_budget_status` resolves through the shim) is
  invisible to CC's code reading — CC reading the habit code_ref would
  look at `wild_igor/igor/tools/budget.py` (a shim) instead of
  `lab/utility_closet/budget.py` (the actual code). Worth a `/context-load`
  enhancement that tells CC "this file is a shim; the real code is here."

## What else?

- **Unit of thought in comms:** a "message" is well-defined (envelope
  + channel + transport). But a "conversation" isn't — there's no
  first-class turn/thread model. TWM, pe_chain, and CC slate each have
  their own notion. A shared `conversation_id` on `ChannelMessage`
  would enable cross-surface continuity, including multi-agent chat on
  the same thread.
- **Small hardware:** the per-message `_channel_append` + Postgres
  round-trip + WebSocket broadcast + subscriber fan-out is 4+ ops per
  message. On a small box under load this adds up. Moving to
  LISTEN/NOTIFY (as the DB persona suggested) would collapse three of
  them into one. The `postgres.py` transport is an obvious home for
  this.
- **Engram review for tools:** habits have code_refs; the simple
  resolver I ran (DB → importlib probe) is the lightest possible
  "engram audit." Wire it into `/day-close-audit` as a daily tripwire.
  For the deeper version Pass 1 persona 12 asked about — "audit the
  engrams themselves" — the tool side is small: 131 PROC habits with
  code_refs is a finite universe that a single Haiku agent could
  review in one pass.

## Summary

- Ticket candidates total: 14
  - New tickets this report: T-uc-http-fallback-single-app,
    T-uc-transport-dependency-inversion, T-misfire-counter-pg-backed,
    T-uc-check-running-last-url-warning, T-mcp-request-compaction-no-tmux,
    T-misfire-taxonomy-expand, T-shim-sunset,
    T-inference-transport-make-context-signature,
    T-toolstats-sample-semantics-fix, T-rack-wire-or-retire,
    T-web-chat-timestamp-prefix-uses-flag, T-mcp-per-host-routing,
    T-discord-transport-webhook-remove, T-machine-manager-lazy-db-url-check,
    T-uc-channel-append-via-comms. (15 including
    T-uc-channel-append-via-comms — count is 15.)
- Revised total: 15 ticket candidates.
- Recommended SHIP: 8
  - T-uc-http-fallback-single-app (correctness)
  - T-misfire-counter-pg-backed (perf + no-SQLite rule alignment)
  - T-mcp-request-compaction-no-tmux (removes brittle path)
  - T-inference-transport-make-context-signature (CRITICAL — transport
    100% broken today)
  - T-toolstats-sample-semantics-fix (silent stat corruption)
  - T-web-chat-timestamp-prefix-uses-flag (follow-through on an
    already-shipped ticket)
  - T-discord-transport-webhook-remove (trivial)
  - T-machine-manager-lazy-db-url-check (unblocks CI/test)
  - T-uc-channel-append-via-comms (layering hygiene)
  - (9 by strict count — I over-counted; let me fix: 9 SHIP.)
- Revised SHIP: 9.
- Recommended DEFER: 3
  - T-uc-check-running-last-url-warning (low value, piggyback)
  - T-misfire-taxonomy-expand (depends on T-misfire-counter-pg-backed)
  - T-shim-sunset (housekeeping; non-urgent)
- Recommended INVESTIGATE: 2
  - T-uc-transport-dependency-inversion (scope is big; Akien should
    decide sequencing against shelf-inversion work)
  - T-rack-wire-or-retire (wire-or-retire decision needs Akien)
  - T-mcp-per-host-routing (verify the localhost fallback is actually
    biting before spending on it)
  - Strict count INVESTIGATE: 3.
- Recommended DISCARD: 2
  - Finding P1-1b (unused imports) — REFUTED at source; actual imports
    are used.
  - Finding P1-1c (naming inconsistency) — the `_tool_*` underscore
    prefix is a consistent house convention, not a bug.
  - Gap 8 (comms.send race) — below the fold; cost > benefit.
  - Strict count DISCARD: 3.

Totals (strict): 15 tickets, 9 SHIP, 3 DEFER, 3 INVESTIGATE, 3 DISCARD
(two of the DISCARDs are verdicts on Pass 1 findings, not tickets).
Ticket candidates (new work items) are 14; the two DISCARD-Pass-1-findings
aren't new tickets.

- Highest-stakes single finding in this area: **Gap 1 —
  InferenceTransport kwargs mismatch.** The comms://model/* and
  comms://or-chat/* paths are currently 100% broken with silent error
  returns. Every chat-channel ticket filed against this transport will
  hit the same TypeError. This needs to ship before anyone builds on
  these surfaces.
- One sentence for Pass 3: Decide the sequencing between
  T-uc-transport-dependency-inversion (cleanup the lab↔wild_igor
  crossings) and T-shim-sunset (finish the already-started inversion) —
  they touch the same layering story from opposite ends and either can
  run first.

Biomimicry verdict on this area: n/a. Comms / UC / tools / MCP is pure
infrastructure. The single place biological language appears is
`misfire_counter` ("misfire") and `scope_guard` ("inhibitor"-adjacent),
and the closer look showed `misfire_counter` is under-ambitious rather
than theatrical — it detects exceptions, not the richer "expected
outcome did not occur" that the name suggests. Fix is in
T-misfire-taxonomy-expand; rename the module only if the taxonomy
doesn't land.
