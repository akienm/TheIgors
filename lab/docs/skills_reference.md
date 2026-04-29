# Skills Reference

**Last updated**: 2026-04-29
**See also**: `glossary.md`, `capability_map.md`

> **In flight:** the audit family is being restructured under
> [D-audit-pyramid-redesign-2026-04-29](../design_docs/decisions/D-audit-pyramid-redesign-2026-04-29.md).
> Current skills below still apply until the rename tickets ship. See the
> "In flight" section at the bottom for the target shape.

Slash-commands available to Akien + Claude. Match each command to *when* in
the day's flow it fires — that's the discipline. If the column "When to
fire" doesn't fit the moment, the wrong command is being used.

---

## Akien-Claude flow (design / decision / day-close)

```
/context-load             │ Start of session         │ Palace briefing + slate + decisions + channel; 2000-token budget
/design                   │ Start of design block    │ OPTIONAL marker — /decided can infer scope without it
/decided                  │ Discussion conclusion    │ Summarize → draft tickets → /review each → file to queue + slate + palace
/fixit                    │ Quick reactive fix       │ /decided + /sprint-batch on the just-filed tickets — single-session shortcut
/ticket                   │ Standalone filing        │ Create/update one ticket; arg "last" = thing just discussed
/note                     │ Non-ticket milestone     │ Log to notes.log + slate (when there's no ticket-shaped output)
/savestateauto            │ End of work block        │ Flush in-flight hypothesis to slate; emit compact preserve string
/savestate                │ End of session           │ /savestateauto + trigger /compact with preserve string
/day-close                │ End of day               │ savestate → close slate → /day-close-audit → fix → docs sync → GitHub Discussion → commit
/day-close-audit          │ Always inside /day-close │ 19-step debris check (tests, files, smells, inertia, logs, burn, schema, dupes, habits, TWM, deps, creds, simplification, wiring, cap-map drift)
/validate-files           │ Standalone / in audit    │ Walk filesystem for misplaced runtime state and code that wrote it wrong
/deep-audit               │ Heavyweight review       │ 11-specialist parallel codebase review
```

---

## Claude-Minion flow (sprint loop)

```
/sprint                   │ One ticket               │ context-load → claim → implement → /test-fix → /commit → close → loop
/sprint-batch             │ Many tickets, one setup  │ Same loop with shared git/venv/env; takes a selector (today-slate, decision:..., tag:...)
/review                   │ Filing-time + standalone │ Called by /decided per-ticket; standalone on diff/PR/plan
/commit                   │ Ad-hoc outside sprint    │ test → stage by name → commit → pull → push
/test-fix                 │ Run + fix + retry        │ pytest → fix failures → retry up to 3× → escalate
```

---

## Igor ops

```
/readinbox                │ Igor → CC messages       │ Read unread CC inbox (auto-checked on /context-load)
/readigor                 │ Igor's recent replies    │ Read Igor's outputs from shared channel; arg = machine (akiendell|yoga9i|yogai7|local)
```

---

## Reference / archive

```
/export-chat              │ On demand                │ Dump current session transcript to claude_chat_logs/YYYY-MM-DD.md
```

---

## Built-in (Claude Code core — not user-defined)

```
/schedule                 │ Recurring / future       │ Cron-style remote agents — "open cleanup PR in 2 weeks", "every Monday triage X"
/loop                     │ Babysit a task           │ Run a prompt or skill on a fixed interval until cancelled
/fewer-permission-prompts │ One-shot setup           │ Scan transcripts → allowlist common read-only bash/MCP in settings.json
/simplify                 │ Code review pass         │ Review changed files for reuse, redundancy, simplification candidates
/security-review          │ Pending diff             │ Security pass on staged changes (run before Igor self-edits land)
/update-config            │ Settings changes         │ Edit settings.json — hooks, permissions, env vars
/keybindings-help         │ Customize keys           │ Edit ~/.claude/keybindings.json
/claude-api               │ Building Anthropic apps  │ Build/debug Claude API code with prompt caching
/init                     │ One-shot                 │ Initialize CLAUDE.md from current codebase
```

---

## Hard rules / load order

- `/context-load` before any work in a fresh session — palace + slate + channel state must be loaded.
- `/day-close-audit` always inside `/day-close` — never skipped; it's the integrity gate.
- `/review` fires per-ticket inside `/decided` — filing-time quality is the whole point.
- `/commit` lives inside `/sprint`, `/sprint-batch`, `/day-close`, or explicit ad-hoc only — never inline during a feature build.
- `/savestateauto` at every work-block boundary; `/savestate` only when the session is actually ending.
- `/fixit` infers scope implicitly from recent turns — use `/decided` (alone) when you want to file but not sprint yet.
- HIGH-inertia file touches surface inline during `/decided` or `/review` for pre-approval; the stamp lands in the ticket body before filing.

---

## What changed since the old reference

| Old skill         | Now                                                                |
|---|---|
| `/slate`          | Manual file at `~/.TheIgors/claudecode/YYYYMMDD.slate.txt`; `/context-load` reads it; `/decided` and `/sprint` append to it. |
| `/slateclose`     | Folded into `/day-close` (which closes the slate as Step 3).        |
| `/filter`         | Folded into `/review` filing-time mode (called by `/decided`).      |
| `/audit`          | Renamed to `/day-close-audit` (2026-04-20) — `/review` is now the skill for reviewing plans/code; `/day-close-audit` is the debris check. |
| `/probe`          | Igor-side; not a CC slash-command. Use `mcp__igor__channel_send` + `mcp__igor__channel_read` for stimulus → response. |
| `/igor`           | Igor-side ops; not a CC slash-command. Use `mcp__igor__*` tools for health/logs/reload from MCP. |

Plus added since the old doc:
- `/design`, `/note`, `/sprint-batch`, `/fixit` (replaces old `/ticket+/sprint` shortcut), `/deep-audit`, `/validate-files`, `/export-chat`
- Built-in: `/schedule`, `/loop`, `/fewer-permission-prompts`, `/simplify`, `/security-review`

---

## Pointers

- Skill source: `~/.claude/skills/<name>/SKILL.md` (user-defined) or built-in.
- Repo echo: `lab/claudecode/cc_skills/` mirrors user skills (auto-synced via pre-commit).
- Authoring a new skill: copy an existing SKILL.md as a template; the next pre-commit picks it up.

---

## In flight — audit pyramid redesign (not yet shipped)

Tracked by [D-audit-pyramid-redesign-2026-04-29](../design_docs/decisions/D-audit-pyramid-redesign-2026-04-29.md).
Current skills above still apply until the rename tickets land. Target shape:

### Renames + folds

| Today                | Becomes                                                          |
|---|---|
| `/day-close-audit`   | `/audit-day` (extended with cross-day watch-for + fix-one-leave-many sweep) |
| `/deep-audit`        | `/audit-expert` (broadest lens per expert, no "mainly look at X") |
| `/validate-files`    | folded into `/audit-debris`                                       |
| `/review` (filing)   | `/audit-ticket` (extended: validation/remediation/rollback/observability) |
| `/review` (sprint)   | `/audit-precode` (NEW — between /sprint plan and first edit)      |

### New layers

| New                  | Role                                                             |
|---|---|
| `/audit-design`      | Called by `/decided` before drafting tickets — catches a "decision" that isn't actually decided |
| `/audit-precode`     | Between `/sprint` plan and first edit — verifies file paths + symbols + HIGH-inertia gates exist |
| `/audit-smell`       | Post-code, pre-test — bare try/except, silent-return-False, fix-one-leave-many call-graph walk, diff-drift AMEND-by-default, deprecated-paths, base-class inheritance |
| `/audit-debris`      | Post-test, pre-commit — folds `/validate-files` + owns docs-update at PR time |
| `/audit-audits`      | Meta-audit weekly — consumes structured telemetry from every layer; recommends rule promotions, layer rebalancing, dead-check retirement, watch-for ROI |

### Sonnet-failure-modes-as-rules

New palace rules backing the audit checks:
- `theigors/rules/inherit-base-class` — every non-library class inherits from the base logging+introspection class (foundation of "no print() anywhere"; logging as easy as print via inheritance, not import).
- `theigors/rules/preferred_paths` — declarative `(deprecated → preferred)` pairs (raw psql → MCP tools, channel.py → IMAP bus, direct DB → db_proxy, etc.). Read by `/audit-precode` and `/audit-smell`.
- New palace branch `theigors/infrastructure/by_area/<area>` — surfaced as a one-screen brief at `/sprint` plan-review (counter to architectural amnesia).

### Telemetry shape

Every audit emits one structured run record per invocation at
`theigors/audits/<level>/runs/<timestamp>` (palace tree).
`/audit-audits` consumes the corpus — no codebase reads at the meta level.
Watch-for notes are first-class palace nodes with TTL.

### Model routing

| Audit            | Model                                |
|---|---|
| `/audit-design`  | Opus (architecture judgment)         |
| `/audit-ticket`  | Haiku (declarative checks)           |
| `/audit-precode` | Haiku → Sonnet on HIGH-inertia       |
| `/audit-smell`   | Sonnet                               |
| `/audit-debris`  | Haiku                                |
| `/audit-day`     | Sonnet                               |
| `/audit-expert`  | Opus per expert (rotated weekly, full panel monthly) |
| `/audit-audits`  | Sonnet weekly, Opus monthly          |

### New visualization skill

| New          | Role                                                                 |
|---|---|
| `/map-igor`  | Haiku, on-demand JSON snapshot of Igor (palace, rules, gates, MCP/IMAP, logs, startup reads, DB schema, runtime tree, processes). Output to `~/.TheIgors/maps/igor-map-<timestamp>.json`. Diff mode: `/map-igor --since=yesterday`. |

### Ship order

Foundation first (rename + telemetry + base-class rule + preferred-paths seed),
then per-layer skill builds, then cross-cutting (sprint infrastructure brief,
model routing, auto-scan-for-rest), then `/map-igor`. The audit-audits skill
gates on telemetry shape landing first.
