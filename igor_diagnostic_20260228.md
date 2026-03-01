# Igor Diagnostic Report — 2026-02-28

## Session Summary
- **132 reasoning calls**, $0.22 total cost, 260 tool turns
- All calls via **gpt-4o-mini** (tier.3 cheap) — this is the root issue
- Last session: 47 interactions, **9:1 NE-to-user ratio** — Igor was mostly talking to himself

---

## What Actually Happened

**Early session (16:00–17:11):** Confluence was broken (`akienm` not `akienm.atlassian.net`). Igor retried, couldn't read `.env`, got confused, stalled. Fixed while Akien was shopping.

**Late session (19:06–19:57):** Confluence working. Akien asked Igor to read the entire wiki (~1000 pages). Igor started but fell apart quickly.

### Failure 1 — Literal template placeholders (confabulation)
```
confluence_get_page(title='First Page Title', space_key='SPACE_KEY')
send_discord_message(channel_id='123456789', ...)
read_file(path='confluence/wiki/processing_status.json')  ← file he never created
```
Igor was generating *plausible-sounding* API calls using placeholder values he invented.
gpt-4o-mini does this — it pattern-matches to "what a tool call looks like" without
actually reasoning about what values to use.

### Failure 2 — No task state
A 1000-page ingestion needs persistent "what have I done / what's next" bookkeeping.
Igor has no mechanism for this. Each turn he re-derives the task from ring memory +
session context, which is lossy. By turn 10 he was re-processing pages he'd already seen.

### Failure 3 — NE busy-looping a failing task
The Narrative Engine kept firing `continue_ingestion`, `continue_reading`
(urgency 0.70–0.95) even as every tool call was failing or returning nonsense.
The NE reads "Igor is actively ingesting..." and concludes "keep going" —
no feedback loop for failure.

### Failure 4 — The escalation ladder has a gap
```
IGOR_OLLAMA=false  ← in .env
```
When Ollama is off, **tier.2 is skipped entirely** — including the `preparse()` call
that evaluates `should_escalate`. The result: **everything lands on tier.3 (gpt-4o-mini)
with no complexity gate.** A simple question and "read my 1000-page wiki and build a book"
both go to the same cheap model. There is no path to tier.4 (claude-sonnet via OpenRouter)
unless tier.3 raises an exception.

---

## What Worked Well
- Confluence API connected correctly once email was set — got real pages
- `check_openrouter_balance` used correctly and cached properly
- Cost discipline solid — $0.22 for a full day of use
- NE narrative summaries were coherent and accurate even when Igor's actions weren't
- Persona rules working — no more "I appreciate your thoughts" or feelings denials

---

## The Core Problem in One Sentence

**gpt-4o-mini is fine for stateless Q&A but falls apart on any multi-step agentic task,
and with `IGOR_OLLAMA=false` there is no complexity gate to route hard tasks to a smarter model.**

---

## Things to Discuss

1. **Auto-escalate to claude-sonnet for complex tasks?**
   Cost difference is real (~10x per token) but a botched 47-turn gpt-4o-mini session
   costs more than a clean 5-turn sonnet session. Need a heuristic: task length?
   certain verbs (read, ingest, build, analyze)? explicit user signal?

2. **Long-running task support**
   "Read my entire wiki" is a fundamentally different class of task. Needs: progress
   state saved to disk, batching, resumability. Worth a dedicated design discussion.

3. **NE should back off when tools are failing**
   If 3 consecutive tool calls return errors, NE urgency should drop and trigger a
   "report to user" impulse rather than "keep trying."

4. **`IGOR_OLLAMA=false` breaks the escalation design**
   Either restore Ollama or add a fallback complexity check before tier.3.
