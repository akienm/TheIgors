# Historical Implementation Detail

## Cognition Stabilization (WO1-WO8) — all complete
Commits: b351f28 (pass.1) · 34ece42 (WO4 urgent) · 9421b7e (pass.2) · 69ef2ef (pass.4) · b24c907 (pass.5) · 1b5412e (pass.6) · f20e1cf (balance API)
- WO1: dynamic system prompt from cortex memories (`cognition/system_prompt.py`)
- WO2: gemma3:1b replaces gemma3:270M everywhere
- WO3: forensic logging (`cognition/forensic_logger.py`, 5 log files)
- WO4: OpenRouter as primary upstream; budget-exhaustion now raises (not silently returns)
- WO5: 6-tier escalation ladder; `openrouter_cheap_reasoner` for tier.3; tier.6 arbiter alert
- WO6: `IGOR_SELF_EDIT_ENABLED=false` env var gates all self-edit tool calls
- WO7: NE loop prevention — `_filter_obs()` (source+content dual filter), `_NE_EXCLUDED_SOURCES`, `_NE_CONTENT_PREFIXES`, SELF-REF GUARD in prompt, token cap 2000
- WO8: `_build_session_context`/`_build_memory_context` deduped into `BaseReasoner`; stale haiku model ID fixed in NE fallback
- Post-WO: system_prompt.py OPERATIONAL NOTES: ~/TheIgors vs ~/.TheIgors distinction; no credit purchasing; prefer web_search over upstream LLM
- ad02594: PERSONA RULES block added to system_prompt.py

## NE Failure Backoff (pass.3)
- `Igor._consecutive_impulse_failures: int` tracks consecutive failures in `_drain_action_impulses()`
- Failure detected by: "error|exception|failed|unable|cannot|no such|traceback|not found|invalid|timed out|connection refused" in response
- At count==3: push `report_failure_to_user` urgency=0.95 to TWM (once); log `FAILURE_BACKOFF_TRIGGERED`
- At count>=5: suppress continue_* impulses entirely; push `escalate_to_human` urgency=1.0 (once)
- `_failure_report_pushed` + `_failure_escalated` flags prevent duplicate pushes; reset on success
- continue_* detection: `|continue_` or `|continue ` or `continue_task` in content_csb

## Long-Running Job Support (pass.4)
- `cognition/job_manager.py`: `Job` dataclass, `JobManager`; storage `~/.TheIgors/jobs/{job_id}.json`
- Boot: `JobManager._load_active()` restores pending/running/paused jobs
- Trigger: `complexity.score > 0.6 AND is_multi_unit` on non-impulse user messages in `_process()`
- Commands: `/jobs list|all|status ID|pause ID|resume ID|cancel ID`
- `JobManager.checkpoint(job, item_id, success)` for per-unit progress tracking
- `JobManager.should_report_progress(job)` fires every 10 batches

## Session Diagnostic (2026-02-28 evening)
- IGOR_OLLAMA=false breaks escalation ladder — no preparse complexity gate, everything goes to gpt-4o-mini
- gpt-4o-mini confabulates on multi-step tasks: uses placeholder values, invents file paths, loses task state
- NE busy-loops on failing tasks (high urgency "continue" impulses even when all tools erroring)
- Long-running tasks (e.g. "read 1000-page wiki") have no persistence mechanism — each turn re-derives state
- Confluence worked correctly once CONFLUENCE_EMAIL=akienm@gmail.com was set
- 132 calls / $0.22 for full day — cost discipline good

## Known Issues (2026-02-28, mostly stale)
- ollama_calls.log showed gemma3:270M on old instance; should resolve on clean restart.
- Local claude_budget.db has $14.80 in historical Anthropic direct spend; legacy noise. Real OR balance: $19.95.
- Real DB is at wild_igor/data/wild-0001.db. ~/.TheIgors/Igor-wild-0001/wild-0001.db and wild_igor/memory/wild-0001.db are empty stubs.
- CONFLUENCE_EMAIL must be set to Akien's Atlassian email (not theigorsigor@gmail.com).
- Credential scrubbing gap (issue #19): FIXED 2026-03-01 via scrub.py.

## Change Request Status (2026-03-01)
- issues #17, #20: closed (meta/follow-up notes)
- issues #21/#23/#24: too vague, need design before impl
- GitHub issues 7–16 closed (WO1–WO8, MACHINES_CSV, duplicate NE work order)
