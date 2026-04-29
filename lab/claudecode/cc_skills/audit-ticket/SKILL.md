---
name: audit-ticket
description: Filing-time ticket audit — extends /review with validation steps, remediation plan, rollback (HIGH-inertia), logging requirements, observability assertion, and split test. Called by /decided on each drafted ticket before filing. Returns PASS / AMEND / SPLIT / DISCARD. Model: Haiku.
model: haiku
---

# audit-ticket — Filing-time ticket quality gate

Extends `/review` filing-time mode with additional checks focused on runtime
observability and cleanup completeness. Every ticket goes through this before
landing in queue.json.

## Input

A drafted ticket dict (id, title, size, tags, description, decision_id).

## Checks (in order — inherit all /review checks, then add)

### 1–8. All /review filing-time checks (run first)

Always run the full `/review` checklist (duplicate, already-done, blocked-by,
size-sanity, scope-creep, HIGH-inertia, palace design-rules, build-tightness).
These are prerequisite — audit-ticket is additive, not a replacement.

### 9. Validation steps (how do we observe success in runtime?)

The description must answer: **how will we know it worked in production, not
just in tests?** Required specifics:
- A log line that signals success (e.g. "STEP3 posted ready for ticket=T-xxx")
- A DB row that appears or changes
- A channel message that fires
- A metric or count that moves

"Tests pass" does not count as a runtime validation step. "The habit fires"
needs a log line to confirm it.

Missing → AMEND: add `Validation: <what runtime observation confirms success>`

### 10. Validation remediation (cleanup after tests)

When the ticket involves DB rows, test fixtures, log files, or network state
that tests create: the description must say how to clean up.

- DB rows: "test fixture teardown via conftest.pg_test_schema"
- Log noise: "test_mode flag suppresses log entries"
- Channel messages: "channel mocked in test"

Silence = AMEND: add `Cleanup: <how test artifacts are removed>`

### 11. Rollback plan (HIGH-inertia only)

When the ticket touches a HIGH-inertia file (brainstem/, memory/models.py,
reasoners/base.py):

- Description must include: "Rollback: `git revert <hash>` restores previous
  behavior because X" (or explain why rollback isn't needed)
- Silence = AMEND

### 12. Logging requirements

Check the description for: does the new code path have a log line that would
immediately point at it when it breaks in production?

Pattern: any `try/except` block, any silent-return-False path, any fanout
(habits, TWM push) — these MUST have a log statement.

If the ticket proposes any of these patterns without a logging requirement,
add: `Logging: try/except at <file>:<lineno> must log ERROR with surrounding
state on exception`

### 13. Observability assertion

Every non-trivial ticket must be able to answer: "If this breaks in prod,
which log line points at it within 5 minutes?"

Required: one explicit log line (level + message) in the description or test
plan that serves as the observability hook.

Missing = AMEND: add `Observable via: log.<level>("<message>") at <location>`

### 14. Split test (size + verb count)

Count distinct action verbs in the check_body:
- add, remove, create, delete, modify, rename, move, update, fix, extend, build

When size > S AND verb count >= 3 in the same semantic unit → propose split.

Output: `SPLIT: propose T-a (verbs X, Y) + T-b (verb Z)`

### 15. Audit-emphasis tag

Does the ticket description include an `audit-emphasis` directive?
- `needs-deep-smell`: flag for extra audit-smell attention
- `doc-only`: skip audit-smell for this ticket (pure doc change)
- Absent: normal audit routing

Note the tag (or absence) in output so downstream audit routing can act on it.

## Output format

```
audit-ticket — <ticket-id>
Verdict: PASS | AMEND | SPLIT | DISCARD
Build-tightness: tight | medium | loose

Checks passed: <N>  
Findings:
- [duplicate] <T-xxx already covers this>
- [validation-steps] runtime observation not specified
- [validation-remediation] test artifact cleanup not specified
- [rollback-plan] HIGH-inertia touch without rollback plan
- [logging-required] try/except at <location> needs ERROR log
- [observability] no observable log line named
- [split] 3+ verbs in one ticket (proposed: T-a + T-b)
- [audit-emphasis] <tag or "none">

Amended ticket (if AMEND): <diff from input>
Child proposals (if SPLIT): <list>
```

## Hard rules

- Always run all /review checks first, then these additions.
- AMEND on missing validation steps — "tests pass" is not a runtime validation.
- SPLIT when verb count ≥ 3 in a ticket > S size.
- HIGH-inertia rollback plan is required — ask Akien if unclear.
- Emit per-run telemetry:
  `from lab.claudecode.audit_telemetry import emit_run_record, AuditRunRecord`
