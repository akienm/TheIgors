---
name: review
description: Filing-time + standalone critical review. Primary use — called by /decided on each drafted ticket (duplicate/already-done/blocked-by/size/scope-creep/HIGH-inertia/palace-design-rules). Also invokable directly on a risky diff/PR/plan, or before a sprint claim. Replaces the old /filter + /review with one skill covering both.
model: haiku
---

# /review — Filing-time + standalone critical review

Two modes; same checks applied to different inputs.

## Mode A — filing-time (called by /decided and /fixit)

Each drafted ticket, BEFORE it lands in queue.json, goes through these
checks. Input: the ticket as a dict (id, title, size, tags, description).
Output: verdict (PASS / AMEND / SPLIT / DISCARD), findings, optionally a
modified ticket dict that `/decided` uses instead of the original.

### Checks (in order)

1. **Duplicate detection** — Always grep `queue.json` for tickets with overlapping id, title, or significant description n-grams across status `pending`, `in_progress`, and recent `done`. When a match exists: output `DISCARD: duplicate of T-xxx (shipped|pending)`, or `AMEND: merge with T-xxx` when the new draft adds material the existing one lacks.

2. **Already-done-in-code** — Always grep the codebase for the key symbols, tool names, and file paths the ticket proposes to add. When they already exist with the described behaviour: output `DISCARD: already implemented in <file>:<line>`. This check catches the "we wrote this last month, forgot, and re-ticketed it" failure mode.

3. **Blocked-by-pending** — When the draft mentions code/features/tools described by another pending ticket, output `AMEND: add gate "<ticket-id>"` so the new ticket doesn't try to sprint before its dependency is real.

4. **Size sanity** — Compare declared size vs description scope:
   - XL declared on ≤300 words of description → flag as possibly not-actually-XL
   - S declared on ≥800 words of description → flag as probably bigger than S
   - L or XL → nudge for breakdown ("does this want to be 2-3 child tickets?"). Output `SPLIT: propose <N> children with <shapes>` when obvious cuts exist

5. **Scope-creep** — Does the description contain multiple separable tickets? ("Also: refactor X", "While we're at it, Y"). When yes: `SPLIT: propose <N> children`.

6. **HIGH-inertia check** — When the description names `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py`, or any other file flagged HIGH-inertia in the rules (check via `memory_get(path='theigors/rules/safeguards')`):
   - ALWAYS ASK AKIEN INLINE: "This ticket touches <file> (HIGH inertia). Pre-approve? y/n/reword"
   - On pre-approve: stamp ticket body with `pre-approved by Akien YYYY-MM-DD for touching <file> — reason: <reason>`
   - On refusal: `AMEND: rescope to avoid <file>`, or `DISCARD`

7. **Design-rule checks (palace-loaded)** — Always load Akien's design rules from the palace at filing time and verify the ticket positively against each. This is the scaffold-not-correct check: rules present at filing time, not expected to be remembered.

   Load the checks (use `memory_list_by_type` / `memory_search` when available; fall back to psql):
   ```
   memory_list_by_type(type="RULE", path_prefix="theigors/rules/ticket_design_checks")
   ```
   Fallback:
   ```bash
   psql postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001 -tA -c \
     "SELECT path, content FROM clan.memory_palace
       WHERE path LIKE 'theigors/rules/ticket_design_checks/%'
         AND path NOT LIKE '%/ticket_design_checks'
       ORDER BY path"
   ```

   Each check node's content has a YAML block at the top with:
   - `applies_when` — predicate: does this check fire for this ticket?
   - `verdict` — optional; `AMEND` (default) or `DISCARD`. Lets a check escalate to DISCARD when the rule is unsalvageable at filing time (e.g. no-sqlite: SQLite is never allowed, so a ticket proposing it is DISCARD, not "please tweak and resubmit").
   - `check_body` — what the ticket draft must contain when the check fires
   - `failure_message` — guidance when the check_body is not satisfied

   For each check:
   1. Always read `applies_when` first. Judge whether it fires against the ticket's title + description + tags. If not, skip.
   2. Read `check_body`. Judge whether the ticket satisfies it.
   3. When satisfied → pass silently.
   4. When not satisfied → record `failure_message` verbatim as a finding, and record the check's `verdict` (default `AMEND` when absent).

   Aggregate across all failed checks: if any failed check has `verdict: DISCARD`, the overall verdict is DISCARD. Otherwise AMEND. List all `failure_message` entries as findings regardless (single aggregated verdict line, not N separate verdicts).

   Current check set (as of 2026-04-21, under `theigors/rules/ticket_design_checks/`):
   `no-sqlite`, `oop-first`, `docs-in-code`, `no-new-memory-schemas`, `test-plan-or-why-not`.

   The palace-loaded check set grows over time; this loader picks up new rules automatically.

8. **Build-tightness grade** — After checks 1-7, always score the description against the 4 structured fields (`Affected files`, `Design rules`, `Scope boundary`, `Test plan` — see `/ticket` `## Description template`). A field counts as **present** only when it is specific and non-trivial:
   - `Affected files`: names at least one concrete path (not "TBD" unless the whole ticket is genuinely discovery-shaped)
   - `Design rules`: names specific palace checks that apply, OR states "none apply" with a one-line reason
   - `Scope boundary`: states what's in scope AND what's out of scope
   - `Test plan`: names specific tests OR gives an explicit "no tests because: …" justification

   Grade by count present:
   - 4/4 → **tight** — advisory note only, no effect on verdict.
   - 3/4 → **medium** — advisory note: `build-tightness: medium — <missing field>`. Does not force AMEND on its own, but counts against PASS when other findings are borderline.
   - ≤2/4 → **loose** — always force AMEND with this verbatim failure message (even when all other checks pass):
     > This ticket makes the builder do design work. Bounce back to designer to tighten before filing. Missing/under-specified: `<list>`. See /ticket `## Description template`.

   The grade always appears on the `Build-tightness:` line of the output. Rationale: well-specced tickets make cheap builders viable; loose tickets push design onto the builder. Making that bar explicit at filing time is the scaffold.

### Output format (filing-time)

```
/review — <ticket-id>
Verdict: PASS | AMEND | SPLIT | DISCARD
Build-tightness: tight | medium | loose

Findings:
- <finding 1>
- <finding 2>

Amended ticket (if AMEND): <diff from input>
Child proposals (if SPLIT): <list of {id, title, size, description-sketch}>
Discard reason (if DISCARD): <one line>
```

### Writes (for T-review-self-learning)

Always record every /review invocation to the `review_findings` table — this
feeds the per-check confidence loop that adjusts salience over time:
```bash
python3 ~/TheIgors/lab/claudecode/review_manager.py write \
  --mode filing \
  --ticket <ticket-id> \
  --verdict <PASS|AMEND|SPLIT|DISCARD> \
  --findings '<finding1>' '<finding2>' \
  --checks '<json>'
```
For standalone mode, use `--mode plan`, `--mode code`, or `--mode pr`
accordingly (with `--plan`, `--commit`, or `--pr` instead of `--ticket`).
Also log to `~/.TheIgors/claudecode/logs/YYYYMMDD.review.log` for human
readability.

## Mode B — standalone (code / plan / PR)

Same checks, different shape of input.

### Plan review

Given a plan-in-conversation (usually triggered pre-/sprint by Akien saying "/review this plan"), walk these in order:
1. **Inertia** — which files will be touched? HIGH-inertia files need justification. Read `memory_get(path='theigors/rules/safeguards')` when unsure.
2. **Tests** — what tests will exist for this? Integration vs mocked? Real-Postgres per `theigors/rules/database`.
3. **Scope** — in vs out. Scope creep?
4. **Simplicity** — standard pattern (registry, queue, observer) vs bespoke?
5. **Reversibility** — can this be undone cleanly when wrong?

### Code / diff review

Given a diff (staged changes or a specific commit range), always check:
1. **Secrets** — no `.env`, keys, passwords, hardcoded paths
2. **Dead code** — commented-out blocks, unused imports, replaced-but-not-removed functions
3. **Debug artifacts** — print statements, temp files, TODO without ticket
4. **Test coverage** — new behaviour ships with new tests
5. **Matches ticket** — diff reflects what the ticket asked for, nothing extra
6. **Inertia violations** — HIGH-inertia files changed without justification

### PR review

`/review <PR#>`: fetch via `gh api repos/<org>/<repo>/pulls/<N>/comments` +
`gh pr diff <N>`. Apply the code-review checklist above.

### Output format (standalone)

```
REVIEW — <plan|code|PR#>
Verdict: PASS | MUST-FIX | DISCUSS

Must-fix: <blocking issues — do not proceed until resolved>
Suggestions: <non-blocking improvements>
```

## Self-learning (T-review-self-learning)

After filing ~10 reviews, always check historical confidence per check
before treating it as authoritative:
```bash
python3 ~/TheIgors/lab/claudecode/review_manager.py confidence --check duplicate --days 30
python3 ~/TheIgors/lab/claudecode/review_manager.py stats --mode filing --days 30
```

Interpretation:
- confidence=1.0 (100%): check is reliable, trust it
- confidence=0.5 (50%): check overridden about half the time, be cautious
- confidence=0.0 (0%): check frequently wrong — always ask Akien before issuing AMEND/DISCARD

Adjust salience accordingly: high-confidence checks (duplicate,
already-done) block harder; low-confidence checks (scope-creep) stay
advisory.

## Hard rules

- Always actually look. "PASS" is a verdict earned by checking, not a default.
- Must-fix items always block sprint/filing until resolved.
- Always record Akien overrides on must-fix with `--override --override-reason <reason>` — the override record is training data for the self-learning loop.
- Filing-time /review runs in seconds (Haiku-shaped checklist work). Standalone /review on a complex plan escalates to Sonnet reasoning when needed.
- Always log every invocation to the review log file — feeds T-review-self-learning's per-check confidence updates.

## Related

- **/decided** — calls /review filing-time mode on each drafted ticket before adding to queue.
- **/fixit** — (after rewrite) same, since /fixit = /decided + /sprint-batch.
- **T-review-self-learning** (gated) — reads the review log to adjust per-flag confidence over time.
