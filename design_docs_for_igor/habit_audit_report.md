# Habit Audit Report — 2026-03-20

## Summary
- Total habits (PROCEDURAL memories): 142
- Check 1 (missing habit_type): 3 issues
- Check 2 (ghost action fields): 3 issues
- Check 3 (broken code_ref): 6 issues
- Check 4 (no dispatch path): 1 issue
- Check 5 (trigger substring traps): 0 issues
- Check 6 (duplicate triggers): 1 issue (3 habits share trigger)
- Bonus — invalid habit_type values: 8 issues

---

## Check 1: Missing habit_type

Habits with no `habit_type` field in metadata. These will default to "action" behavior
which emits debug noise ("Habit executed. [...]") and may dispatch unexpectedly.

| id | narrative (first 60 chars) |
|----|---------------------------|
| `295ff92b-975b-4484-8704-91a0dd4a4d70` | PRINCIPLE: Right tool for each job. Local Ollama/pool... |
| `PROC_BROWSE_READING_PURPOSE` | browse_as_employer is for reading as a person reads — ebooks... |
| `PROC_GO_LEARN` | When asked to learn about a topic, search Calibre library... |

Notes:
- `295ff92b-...` has only `key`, `tags` fields — looks like a factual/principle memory that was stored as PROCEDURAL by mistake. No trigger, no dispatch path.
- `PROC_BROWSE_READING_PURPOSE` has an `action` and `trigger` — likely meant to be `habit_type: "response"` or `"action"`.
- `PROC_GO_LEARN` has both `action` and `code_ref` — likely `habit_type: "action"`.

---

## Check 2: Ghost action fields

Habits where the `action` field contains a Python function name or a code-ref path instead
of user-visible text. These will emit the raw function name or module path to the user
if the habit fires without a code_ref dispatch path.

| id | narrative (first 60 chars) | action value |
|----|---------------------------|--------------|
| `PROC_EXIT_IGOR` | When Akien says 'exit igor', 'shutdown igor'... | `exit_self` |
| `PROC_READ_NOW` | When Akien sends me a URL, a file path, or says 'read this'... | `tools.ebook_reader:start_foreground_reading` |
| `PROC_STOP_READING` | When Akien says 'stop reading', 'stop background reading'... | `tools.ebook_reader:stop_foreground_reading` |

Notes:
- `PROC_EXIT_IGOR`: `action='exit_self'` is a raw function name. The habit also has a `code_ref` that is itself broken (see Check 3). The action field should be a canned response like `"Understood, Mashter. Shutting down cleanly."` or removed.
- `PROC_READ_NOW` and `PROC_STOP_READING`: `action` is identical to `code_ref`. The action field should be a short user-facing confirmation string (e.g., `"Opening that now, Mashter."`), not the dispatch path. Since `code_ref` is present and valid, the `action` field here is just redundant noise — but if code_ref dispatch ever fails, the raw path would leak to the user.

---

## Check 3: Broken code_ref

Habits where `code_ref` points to a module or function that does not exist in the codebase.

| id | code_ref | reason |
|----|----------|--------|
| `PROC_CLUSTER_SSH_CHECK` | `tools.cluster_ssh:cluster_status` | Function `cluster_status` not in `cluster_ssh.py`. The public function is `get_cluster_loads`; `cluster_status` exists only in `runner.py`. |
| `PROC_DISK_USAGE_CHECK` | `tools/filesystem.py:check_disk_usage` | Slash-style path not a valid code_ref format. Function exists in `filesystem.py`; correct ref is `tools.filesystem:check_disk_usage`. |
| `PROC_EXIT_IGOR` | `tools.runner.exit_self` | Missing colon separator — should be `tools.runner:exit_self`. Function `exit_self` does exist in `runner.py`. |
| `PROC_HABIT_BUDGET_CHECK` | `tools.budget:get_budget_status` | Function `get_budget_status` not in `budget.py`. Closest match is `budget_status`. |
| `PROC_NIGHT_READ` | `drain_learn_queue` | No module path and no colon. Bare function name — module not specified. Likely meant `tools.learner:process_learn_queue` (which exists and is used by `PROC_NIGHT_LEARN_QUEUE`). |
| `PROC_SET_CLOUD_NOW` | `set_cloud_ok_override` | No module path and no colon. Function `set_inference_override` exists in `runner.py` but name doesn't match. |

---

## Check 4: Habits with no dispatch path

Habits where `habit_type` is "action" or missing, AND none of `action`, `actions`, `code_ref`
are present. These will fire and emit "Habit executed. [...]" debug noise with no output.

| id | habit_type | narrative (first 80 chars) |
|----|------------|---------------------------|
| `295ff92b-975b-4484-8704-91a0dd4a4d70` | *(missing)* | PRINCIPLE: Right tool for each job. Local Ollama/pool for reasoning and text... |

Note: This memory has no trigger either (see bonus findings). It appears to be a principle/factual
memory misfiled as PROCEDURAL. It would not fire in practice, but `memory_type` is wrong.

---

## Check 5: Trigger substring traps

No issues found. All triggers examined are either:
- Multi-word phrases unlikely to match unintended input, or
- Internal event tokens (e.g., `routing_decision`, `backup_check`) not matched against raw user text.

---

## Check 6: Duplicate triggers

One trigger string is shared across 3 different habits:

| trigger | habit ids |
|---------|-----------|
| `routing_decision` | `PROC_ROUTING_ESCALATE`, `PROC_ROUTING_INTERACTIVE`, `PROC_ROUTING_LOCAL` |

Note: All three are `passive_capture` habits for different routing scenarios. The trigger
`routing_decision` is an internal event token, not a user-input pattern. The duplication is
likely intentional — all three should capture on this event. However, if the habit scorer
only fires the highest-scoring match, two of the three will silently be skipped. Worth
confirming the scoring behavior handles parallel passive_capture firing correctly.

---

## Bonus: Invalid habit_type values

Eight habits use `habit_type` values not in the canonical set
(`threshold | action | workflow | delegation | reactive | response | question | context_inject | cognitive | tool | passive_capture`).

| id | habit_type | narrative (first 60 chars) |
|----|------------|---------------------------|
| `PROC_BACKUP_CHECK` | `proactive` | Periodically check when the last backup was made... |
| `PROC_PROACTIVE_HABIT_REVIEW` | `proactive` | Periodically review recently stored memories... |
| `PROC_PROACTIVE_RING_REVIEW` | `proactive` | Every hour, scan recent ring buffer entries... |
| `PROC_WATCH_FOUND_COINS` | `watch` | When Akien mentions finding something valuable... |
| `PROC_WATCH_INWARD_CLAIM` | `watch` | When I make causal or explanatory claims... |
| `PROC_WATCH_INWARD_FACTUAL` | `watch` | When I cite external sources or appeal to research... |
| `PROC_WATCH_INWARD_UNCERTAIN` | `watch` | When I express uncertainty... |
| `PROC_WATCH_LEAH` | `watch` | Leah is Akien's wife. When she comes up in conversation... |

Notes:
- `proactive` type: These three habits also use `schedule: interval:N` — they appear designed for
  a periodic scheduler that may not yet be implemented. They will not fire via the standard
  BG habit scorer. The `action` fields contain detailed LLM instructions (multi-sentence),
  suggesting they're meant to be injected as prompts. `passive_capture` or `cognitive` may be
  more appropriate until a scheduler is built.
- `watch` type: Five habits use `watch_type` and `watch_label` fields suggesting a dedicated
  Watcher subsystem (referenced in MEMORY.md). These habits will not dispatch via standard
  habit scoring either. If the Watcher service isn't active, these are silent dead weight.
  They are otherwise well-formed (triggers look correct, metadata is clean).

---

## Bonus: Habits with no trigger

Four habits have no `trigger`, `triggers`, or `auto_fire_on` field. Without a trigger, these
cannot be matched by the BG habit scorer against user input or internal events.

| id | habit_type | narrative (first 70 chars) |
|----|------------|---------------------------|
| `295ff92b-975b-4484-8704-91a0dd4a4d70` | *(missing)* | PRINCIPLE: Right tool for each job. Local Ollama/pool... |
| `HABIT_20260308T211614` | `action` | CC: CC> All verified: - **Phase 1 was already complete**... |
| `PROC_DIRECTION_AWARE` | `cognitive` | Notice what traversal direction you've been taking... |
| `PROC_NIGHT_READ` | `threshold` | At night (22:00–07:00), if I have items in the learn queue... |

Notes:
- `295ff92b-...`: No trigger, no dispatch. Dead memory — consider reclassifying as FACTUAL or INTERPRETIVE.
- `HABIT_20260308T211614`: Appears to be a stale/accidental habit record from a CC session log. No trigger, `action` is a raw CC conversation snippet. Candidate for deletion or reclassification.
- `PROC_DIRECTION_AWARE`: `cognitive` type with no trigger. May be intended as a context_inject or passive_capture that fires automatically, but without trigger or auto_fire_on it won't.
- `PROC_NIGHT_READ`: `threshold` type — threshold habits are evaluated by `ResourceMonitorSource` using `condition_field/op/value`, not user-input triggers. The missing trigger is expected. However, `condition_field: night_mode` is not a standard field documented in `ResourceMonitorSource`; the broken `code_ref: drain_learn_queue` (Check 3) means it cannot dispatch even if the condition were met.

---

## Recommended fixes

| Habit id | What to change |
|----------|---------------|
| `295ff92b-975b-4484-8704-91a0dd4a4d70` | Change `memory_type` from PROCEDURAL to FACTUAL; or delete — it is a principle with no trigger or dispatch path. |
| `PROC_BROWSE_READING_PURPOSE` | Add `habit_type: "action"` (has action + trigger, just missing the type field). |
| `PROC_GO_LEARN` | Add `habit_type: "action"` (has action, trigger, and valid code_ref). |
| `PROC_EXIT_IGOR` | Fix `code_ref` from `tools.runner.exit_self` to `tools.runner:exit_self`. Replace `action: "exit_self"` with a canned confirmation string, e.g. `"On it, Mashter. Shutting down cleanly."` |
| `PROC_READ_NOW` | Replace `action: "tools.ebook_reader:start_foreground_reading"` with a canned string, e.g. `"Opening that now, Mashter."` (code_ref already handles dispatch correctly). |
| `PROC_STOP_READING` | Replace `action: "tools.ebook_reader:stop_foreground_reading"` with a canned string, e.g. `"Stopped reading, Mashter."` (code_ref already handles dispatch). |
| `PROC_CLUSTER_SSH_CHECK` | Fix `code_ref` from `tools.cluster_ssh:cluster_status` to `tools.runner:cluster_status` (function exists in runner.py, not cluster_ssh.py). |
| `PROC_DISK_USAGE_CHECK` | Fix `code_ref` from `tools/filesystem.py:check_disk_usage` to `tools.filesystem:check_disk_usage`. |
| `PROC_HABIT_BUDGET_CHECK` | Fix `code_ref` from `tools.budget:get_budget_status` to `tools.budget:budget_status`. |
| `PROC_NIGHT_READ` | Fix `code_ref` from `drain_learn_queue` to `tools.learner:process_learn_queue`. Confirm `condition_field: night_mode` is a real field evaluated by ResourceMonitorSource. |
| `PROC_SET_CLOUD_NOW` | Fix `code_ref` from `set_cloud_ok_override` to `tools.runner:set_inference_override` (if that is the intended function; verify). |
| `PROC_BACKUP_CHECK` | Change `habit_type: "proactive"` to `"cognitive"` or `"passive_capture"` until a scheduler service exists; or confirm the proactive type is handled somewhere. |
| `PROC_PROACTIVE_HABIT_REVIEW` | Same as PROC_BACKUP_CHECK. |
| `PROC_PROACTIVE_RING_REVIEW` | Same as PROC_BACKUP_CHECK. |
| `PROC_WATCH_*` (5 habits) | Confirm Watcher subsystem is active. If not, these habits are unreachable. No immediate fix needed — document as deferred until Watcher is wired in. |
| `HABIT_20260308T211614` | Delete or reclassify — accidental action habit with no trigger and a CC conversation fragment as its action text. |
| `PROC_DIRECTION_AWARE` | Add `trigger` or `auto_fire_on` so the cognitive habit can fire; or change to `context_inject` if it should be injected on every relevant turn. |
| `PROC_ROUTING_ESCALATE / INTERACTIVE / LOCAL` | Verify BG scorer fires all three `passive_capture` habits on `routing_decision` (not just the top scorer). If not, consider consolidating into one passive_capture with branching logic. |
