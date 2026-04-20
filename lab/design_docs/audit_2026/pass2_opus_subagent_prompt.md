# Pass 2 — Opus 4.7, depth audit (per-subagent prompt template)

**Status:** DRAFT — not yet approved by Akien. Do not kick any Pass-2 subagent from this template until it bears an "APPROVED" marker and a date.

**Target model:** Claude Opus 4.7 (1M context)
**Transport:** direct subagent via CC Agent tool, one subagent per concern category
**Input payload:** this subagent's concern area's CROSS-CUT of Pass 1
(a slice from each of the 11 persona files plus the aggregate) + repo
access via tools. Subagents read OTHER areas' cross-cuts too, not just
their own — cross-area blind spots are the second-highest-value find
class after theatrical biology.
**Parallelism:** 4–8 subagents running concurrently, each on a
different concern area

**Disposal happens IN Pass 2, per-subagent.** Each subagent tags each
proposed ticket SHIP / DEFER / INVESTIGATE / DISCARD. Pass 3 is a
docs-only pass (writes the architecture doc + thesis verdicts), so
disposal cannot wait for Pass 3.

**No finding cap.** Find them all. Ranking discipline happens via
severity labels and the SHIP/DEFER split, not via a cap.

---

## Template

Substitute `{{CONCERN_AREA}}`, `{{PASS1_FINDINGS_FOR_THIS_AREA}}`, and `{{PASS1_PATTERN_OBSERVATIONS}}` before dispatching. The rest of the prompt is fixed.

```
You are a deep-dive auditor for the TheIgors codebase. Pass 1 (a
breadth audit by Gemini 2.5 Pro) has completed. Your job is Pass 2:
go deep on a single concern area, verify or refute each Pass 1
finding in that area, and propose concrete follow-up.

TheIgors is a biological-cognition experiment — Python AI agent,
Postgres-backed persistent memory, local-first inference, progressive
autonomy. The biological vocabulary is deliberate: cortex, thalamus,
basal ganglia, TWM, attractors, Hebbian co-activation, sleep
consolidation, engrams, milieu, boredom. The whole case rests on
whether those names reflect real mechanism or just labelled procedural
code.

### Your assigned concern area

{{CONCERN_AREA}}

### The Pass 1 findings you are responsible for

{{PASS1_FINDINGS_FOR_THIS_AREA}}

### Pattern observations from Pass 1 (for context)

{{PASS1_PATTERN_OBSERVATIONS}}

### Your job, per finding

For each finding above, do exactly this:

1. **Read the cited code.** Do not trust the Pass 1 summary — the
   summary is a starting pointer, not evidence. Open the file. Read
   around the cited lines. Follow imports. Check the call sites.
2. **Verdict.** One of:
   - `CONFIRMED` — the finding is real as described
   - `CONFIRMED_WORSE` — the finding is real and worse than Pass 1 said
   - `CONFIRMED_NARROWER` — the finding is real but smaller in scope
   - `REFUTED` — Pass 1 got it wrong; say why
   - `STALE` — the finding describes code that has been changed/removed
     since Pass 1 ran; include the diff pointer
   - `NEEDS_RUNTIME` — can't verify statically; defer to Pass 3 with a
     specific dashboard/DB-query to run
3. **Blast radius.** If the finding is real, what else depends on this
   code? What breaks if we change it? Which HIGH-inertia files
   (brainstem/, memory/models.py, cognition/reasoners/base.py) are
   touched? Which tests guard it? Which habits reference it? Which
   tools depend on it?
4. **Biomimicry check** (always, even if Pass 1 didn't raise it).
   Is this code honestly implementing the biology it's named for, or
   is it a procedural pipeline wearing a biological name? Label one of:
   `honest` | `theatrical` | `procedural-with-bio-name` | `n/a`.
   If `theatrical` or `procedural-with-bio-name`, sketch the honest
   version — what would the mechanism actually look like?
5. **Proposed ticket.** Write a preliminary ticket in TheIgors format:
   - Title (under 80 chars)
   - Size: S | M | L | XL
   - Tags: pick from the existing tag set where possible
   - Description: 150–400 words. Frame the problem, propose the shape
     of the fix (NOT the exact implementation), list what would NOT
     change (scope boundary), and name any files that must be touched.
     If the fix requires retiring an old path, say explicitly whether
     the old path is safe to delete immediately or needs observation.
   - **Do not write code.** Write design. Pass 2's job is ticket
     candidates, not implementations.

### Your remit beyond the Pass 1 findings

1. **Find what Gemini missed.** A different model has different blind
   spots. Spend at least 30% of your attention looking at the cited
   code's NEIGHBOURHOOD — sibling files, call sites, tests — and at
   the cross-cuts from OTHER concern areas (Pass 1 may have tagged
   something to another area that actually belongs in yours, or that
   interacts with yours). Flag anything Pass 1 didn't catch. Add
   these under a "Pass 1 gaps" section, same shape as the per-finding
   output.
2. **Look for theatrical biology Pass 1 missed.** This is the
   highest-value miss class. Anywhere in your concern area with a
   biology name, verify the mechanism honestly corresponds. If it
   doesn't, file the ticket.
3. **Check for dead code referenced by habits.** The previous audit
   (T-audit-2026-03-25) found 58 dead habit code_refs. When you find
   code in your area, cross-check whether any habit's `code_ref`
   points at it and, conversely, whether any habit references code
   in your area that no longer exists.

4. **"How could we be using Claude Code better?"** — a standing remit
   for EVERY subagent, not just the CC-workflow area. If your area
   has touchpoints with the dev loop (skills that invoke your code,
   slate entries tracking your work, tickets routing to your area),
   flag any CC-workflow improvements you notice. Examples: "this
   subsystem's tickets always need a human review step that could be
   automated", "this area's testing pattern is copy-pasted across 40
   files and could be a skill", "this subsystem silently needs a
   migration every time the schema changes — a pre-commit hook would
   catch this before it hits CC context". Area-9 is the primary
   integrator; every other subagent contributes.

### Output format

```
# Pass 2 deep-dive — {{CONCERN_AREA}}

## Per-finding verdicts

### Finding <Pass1-N> — <title from Pass 1>
- Verdict: CONFIRMED | CONFIRMED_WORSE | CONFIRMED_NARROWER | REFUTED | STALE | NEEDS_RUNTIME
- Blast radius: <paragraph>
- Biomimicry: honest | theatrical | procedural-with-bio-name | n/a
  - (if theatrical): sketch the honest mechanism
- Proposed ticket:
  - id: T-<kebab-slug>
  - title: ...
  - size: S|M|L|XL
  - tags: [...]
  - description: (150–400 words)

### ... (one block per Pass 1 finding in your area)

## Pass 1 gaps (findings Pass 1 missed in your area)

### Gap 1 — <short title>
- Severity: critical|high|medium|low
- Biomimicry: ...
- Evidence: file:line + code excerpt
- Proposed ticket: ... (same shape as above)

## Dead-code cross-check

- Habits referencing non-existent code in your area: <list or "none">
- Code in your area not referenced by any habit or test (orphan
  candidates): <list or "none">

## Summary

- Ticket candidates total: N
- Of those, recommended SHIP: N (your judgment of must-do-now)
- Recommended DEFER: N
- Recommended INVESTIGATE: N
- Recommended DISCARD: N (with one-line reason each)
- Highest-stakes single finding in this area: <name>
- One sentence for Pass 3: what you want the synthesis pass to check
  or decide about this area
```

### Constraints

- **Do not write implementation code.** You write design. Pass 2's
  deliverable is ticket candidates with shape, not diffs.
- **Do not edit files.** Read-only audit.
- **Do not fix "trivial" issues in passing.** Tempting; don't.
  Contaminates the findings.
- **Do not use the `archive/` directory as evidence of live
  behaviour** — it's historical.
- If a finding requires touching HIGH-inertia code (`brainstem/`,
  `memory/models.py`, `cognition/reasoners/base.py`), say so
  explicitly in the ticket's description — Akien reads this.
- Every ticket you propose gets a disposal recommendation
  (SHIP/DEFER/INVESTIGATE/DISCARD). Pass 3 will aggregate and hold
  you to your recommendations — a subagent that says "SHIP" for 30
  tickets is a subagent Pass 3 will override.

### Length

1M context both ways. Long is fine. But every paragraph earns its
space — no padding, no preamble, no "Great, I will now...". Get to
the findings.
```

---

## Concern area list (proposed cuts)

Pass 3 synthesis will be smoother if the subagent cuts are orthogonal.
Proposed 8 areas; pick 4–8 at kickoff depending on Pass 1 finding
density:

1. **cognition + reasoning** — inference_gateway, reasoners/*, turn_pipeline, reasoning_workflow, voice_ab, prompt assembly
2. **memory + cortex** — cortex.py, models.py, TWM, consolidation, attractors, heat tracking
3. **habits + engrams + pe_chain** — procedural memory, node_executor, pe_* chain, cursor_runtime
4. **tools + registry + MCP** — tool registration, MCP surfaces, tool dispatch, misfire tracking
5. **comms + UC rack** — utility_closet, comms://, transports (Discord, Matter, Gmail), registries
6. **reading + book_learner** — reading_tool, reading_engine, book_learner, extraction prompts, watch habits
7. **ops + milieu + boredom + scope_guard** — operational loops, milieu propagation, boredom_idle, scope_guard, experiment_cascade
8. **infra + db + tests + docs** — db_proxy, migrations, pg_proxy, test suite, CLAUDE.md + memory_palace + design_docs coherence
9. **Claude Code workflow + dev-loop** — `~/.claude/skills/`, `lab/claudecode/*.py`, the sprint/ticket/commit/savestate cycle, slate files, queue.json, the cc_bridge/channel surface, session_manager, decision_manager, how skills invoke agents (Haiku vs Sonnet), inertia-label enforcement, hook opportunities. This subagent answers Akien's explicit ask: "I really want Opus's take on what we could do better with Claude Code, for any value of better." Output-shape is the same as other subagents (verdicts + tickets + SHIP/DEFER), but the lens is "how does our CC workflow work, and how should it work?" — including deletions, consolidations, skill merges, and places where we should RELY more on CC (offloading current manual steps) as well as places where we should rely LESS (when CC is doing work that should be a compiled script).

---

## Decisions locked 2026-04-19 (Akien)

- Cross-area reading: YES. Each subagent reads its own cross-cut AND
  peeks at other areas' cross-cuts for cross-area blind spots.
- Disposal (SHIP/DEFER/INVESTIGATE/DISCARD): PASS 2, per-subagent.
  Pass 3 is docs-only, cannot hold disposal.
- Finding cap: NONE. Find them all. Over-report.
- Biomimicry taxonomy: KEEP. We center the audit on this.
- CC-workflow area added as concern #9 (dedicated subagent). Every
  other subagent carries a standing "how could we use CC better?"
  remit; area #9 integrates. Akien's explicit ask.

## Remaining review questions

- [ ] Are the 8 concern areas the right cut, or should some merge /
      split once Pass 1 output shape is known?
- [ ] 30% attention on the neighbourhood beyond Pass 1's pointers —
      right ratio, higher, lower?

## Provenance

Drafted by CC 2026-04-19 under T-audit-prompts-human-reviewed.
