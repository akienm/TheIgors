# Skills Reference

**Last updated**: 2026-04-27
**See also**: `glossary.md`, `capability_map.md`

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
