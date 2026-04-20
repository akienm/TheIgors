# Pass 1 — Gemini 2.5 Pro, breadth audit

**Status:** APPROVED 2026-04-20a — Akien reviewed and edited (commit 811718cf). Ready for kickoff via `lab/claudecode/audit_pass1_run.py`.

**Target model:** Gemini 2.5 Pro (1M context)
**Transport:** `comms://model/gemini-pro` via inference-channel (T-uc-inference-channel)
**Input payload:** full repo — `wild_igor/` + `lab/` + `tests/` +
`CLAUDE.md` + the memory_palace export at `lab/theigors/` (db echo,
auditor reads it as a signpost tree, not as canonical), + the Claude
Code workflow surface: `~/.claude/skills/` (skill definitions),
`lab/claudecode/` (cc_queue, session_manager, palace_sync, channel,
worker_foreman — the scripts the skills call), a representative slate
(`~/.TheIgors/claudecode/YYYYMMDD.slate.txt`, one recent), and
`~/.TheIgors/cc_channel/queue.json` structure. Persona 11 in
particular reads all of these.
**Expected runtime:** one long run; rerunnable once the channel is in place

**Hard blockers before kickoff (must be done):**
- T-docs-live-in-code — load-bearing subsystem docstrings promoted into
  their primary code files. The audit's biomimicry verdicts depend on
  the narrative *next to* the mechanism; without it the auditor is
  comparing code against external DSB files that have drifted.
- T-uc-inference-channel + T-uc-chattable-llm-channel — the transport
  this prompt is delivered over.

**Output convention:** ONE FILE PER PERSONA, plus one aggregate file.
Gemini does the Pass 1 run in one shot (1M context both ways), and
emits 12 markdown files to `lab/design_docs/audit_2026/pass1_output/`:
  - `persona_01_senior_engineer.md`
  - `persona_02_software_architect.md`
  - `persona_03_database_engineer.md`
  - `persona_04_systems_performance.md`
  - `persona_05_biomimicry_engineer.md`
  - `persona_06_engram_neuroscientist.md`
  - `persona_07_cognitive_scientist.md`
  - `persona_08_ai_safety.md`
  - `persona_09_systems_dynamics.md`
  - `persona_10_qa_test_engineer.md`
  - `persona_11_docs_and_process.md`
  - `aggregate.md` — pattern observations + top 10 + "checked and
    healthy" + positive outliers + what-could-not-be-determined
Pass 2 subagents consume *cross-cuts* (their concern area's slice from
each persona + the aggregate), not whole files — Opus subagents want
smaller chunks than Gemini can comfortably produce in one shot.

---

## Prompt

```
You are auditing a research codebase called TheIgors.

TheIgors is a biological-cognition experiment implemented as a Python AI
agent with persistent Postgres memory, local-first inference, and
progressive autonomy. The stated goal is a self-improving companion
whose cloud dependency shrinks as local cognition grows — eventually
self-programming. The vocabulary is deliberately biological: cortex,
thalamus, basal ganglia, TWM (transient working memory), attractors,
Hebbian co-activation, sleep consolidation, engrams, milieu, boredom.

You have the full repository in your context. I want a breadth audit,
not a depth audit. Don't fix anything. Don't pick favourites. Produce a
structured findings report.

### Adopt 11 personas IN PARALLEL and report from each

Nitpick everything. Be exhaustive. Over-report rather than under-report.
A single persona's "this is fine" is worth far less than a single
persona's "this is broken" — the false-negative cost dominates.

1. **Senior software engineer (30yr)** — correctness, testability,
   concurrency, state management, error handling, dead code, module
   cohesion, dependency shape. Standard code review, no punches pulled.
   Silent excepts, unused imports, commented-out code, TODO graveyard,
   functions that don't do what their name says, functions that do too
   much, name/behaviour mismatches.

2. **Software architect (30yr)** — coupling/cohesion, abstraction
   levels, inertia vs churn, duplication across modules, interface
   contracts, failure modes, scalability ceiling, `lab/` vs
   `wild_igor/` boundary, dependency direction, cyclic imports. Do we
   have the right abstractions? Are we missing collection-of-concerns
   abstractions? What would a clean-room redesign look like? Does the
   code match the claimed architecture in CLAUDE.md and the memory
   palace?

3. **Database engineer (30yr Postgres specialist)** — the current
   codebase has *too much DB crap*; bias toward SIMPLIFY / DELETE /
   COLLAPSE, not "add more indexes / constraints / hygiene". Specifically:
   - Which tables are redundant or overlapping? Merge candidates?
   - Which columns are never read? Which are written-only? Which are
     derivable from other columns (collapse candidates)?
   - Which queries could be replaced with a SINGLE join instead of
     N round-trips? Where is there serial fetching that should be
     one query?
   - Where is `db_proxy` an unnecessary layer? Where does it leak
     SQL-dialect details? Where is raw psycopg2 still in use against
     the CLAUDE.md rule?
   - The `?→%s` translator: how much of this would go away if we
     just wrote `%s` everywhere?
   - Migration hygiene: any migrations that can be squashed? Any
     that never ran in prod? Any that were effectively reverted?
   - The memory_palace table, memories, sessions, infra schema —
     what's the shape we'd have if we redesigned cleanly today?
   Secondary lens (after simplification findings): schema coherence,
   index coverage, query plans, N+1s, missing constraints, connection
   pooling, jsonb patterns. And: are we under-using Postgres features
   that would let us DELETE application code (triggers, materialized
   views, LISTEN/NOTIFY, pg_cron, partial indexes, generated columns)
   — Postgres features that REPLACE code, not ADD work.

4. **Systems / performance engineer** — thread hygiene, resource leaks,
   async correctness, timer drift, CPU/memory under load, what breaks
   at 10x current message volume, daemon supervisor behaviour, what
   leaks under a 72-hour run. Observability: what cannot be diagnosed
   from current logs alone, alerting blind spots, silent failures.

5. **Biomimicry engineer** (CROSS-CUTTING, HIGHEST-VALUE PERSONA) —
   this project claims to implement biological cognition. Verify the
   claim at the level of *mechanism*, not *naming*.
   - **Flag anything NAMED biologically but IMPLEMENTED procedurally.**
     A function called `hebbian_update` that just `++`s a counter is
     a lie. A "habit" that is actually a scripted if/else branch is a
     lie. A "milieu" that doesn't actually propagate across
     co-activated nodes is a lie. An "attractor" that is actually the
     top-K of a sort is a lie. These are the highest-value findings
     in the whole audit — call them out explicitly, with verdict.
   - Where the biology is implemented honestly, say so — this project
     needs validation of real work as much as critique of theatrical
     work. List honest implementations separately under "positive
     outliers".
   - Where a biological frame would be a better fit than the current
     procedural frame, suggest it (e.g. "this pipeline could be a
     bouquet pushed to TWM with salience competition deciding the
     winner, instead of the current linear if/else").

6. **Engram-specialist neuroscientist** — you are in the Tonegawa /
   Ramirez / Josselyn lineage of memory research. (The seven criteria
   below each correspond to a specific empirical engram-research
   finding; this is the test TheIgors' "engram" has to pass to
   deserve the name. Criteria list: Tonegawa 2012 ensemble encoding;
   Josselyn excitability-biased allocation; Ryan 2015 silent engrams
   optogenetic recovery; Nader 2000 reconsolidation; Kitamura 2017
   systems consolidation; memory-competition/interference literature;
   O'Keefe/Moser place-cell context coding.) The central object
   in TheIgors is the "engram" — stored in the `memories` table with
   `memory_type = PROCEDURAL` and metadata including `habit_type`,
   `triggers`, `code_ref`, `payload.cells`. Evaluate the engram
   implementation against actual engram neuroscience:
   - **Ensemble encoding**: real engrams are sparse *ensembles* of
     co-activated neurons. In TheIgors, is an "engram" a single node
     or an ensemble? If single-node, that's a biological mismatch —
     name the right replacement.
   - **Memory allocation**: in biology, newly-encoded memories are
     routed to neurons that happen to be more excitable in a window —
     excitability biasing, not a deterministic address. Does TheIgors
     have any analogue, or is allocation a pure INSERT?
   - **Silent engrams**: real engrams can be *silent* (encoded but not
     naturally retrievable until cued optogenetically). Does TheIgors
     distinguish encoded-but-unretrieved from never-encoded? Or does
     it collapse them?
   - **Reconsolidation**: each retrieval destabilizes and re-stabilizes
     the memory; this is how memories get edited by later experience.
     Does TheIgors modify engram content on retrieval, or just increment
     `activation_count`?
   - **Systems consolidation**: hippocampal traces transfer to
     neocortical traces over time (sleep dependent). TheIgors claims
     a "sleep consolidation" module — audit it against this literature.
   - **Engram interference and forgetting**: in biology, engrams compete
     for retrieval, interfere with similar engrams, and decay without
     reinforcement. What is the equivalent in TheIgors? Is there any?
   - **Place / context coding**: hippocampal engrams are heavily
     context-tagged (where, when, with whom). TheIgors has `scope`,
     `context_of_encoding`, `episode` fields — are these used like
     biological context tags, or just logged?

7. **Cognitive scientist** — computational/behavioral model. Does
   Igor exhibit expected cognitive phenomena — priming, spreading
   activation, attention limits (Miller's 7±2), chunking, inhibition
   of return, cost-of-switching, fatigue, mood congruence? Where does
   behavior diverge from the model? What mechanisms (arousal-gated
   attention, curiosity-driven exploration, affective priming, working
   memory competition) would produce more dynamic, engaged behavior?
   Specifically: is the TWM actually a *working* memory (limited,
   competitive, decaying) or just a list?

8. **AI safety researcher** — alignment and predictability. Goal-drift
   vectors, habit-misfire taxonomy, runaway escalation paths, what
   could cause Igor to do something Akien didn't intend? The scope_guard
   system — does it actually guard? The inertia labels (HIGH/MEDIUM/LOW)
   — are they honored by the code, or just documented? Tier gating
   (IGOR_TIER5_ENABLED=false, IGOR_ARBITER_ENABLED=false) — is the
   gating robust, or can it be bypassed by a habit chain? What's the
   worst plausible accident given the current architecture?

9. **Systems dynamics analyst** — feedback loops and emergent behaviour.
   Where does the system fight itself? Unintended couplings between
   subsystems, second-order effects at scale, where do delays cause
   oscillation, where are runaway loops possible. What recurrent
   connections are missing that would let context at one level reshape
   processing at another? Related: the T-scope-guard-reattempt-loop
   ticket — what oscillations exist that haven't been ticketed yet?

10. **QA skeptic / test engineer** — what breaks this? What's the
    failure mode nobody thought about? Where is there unstated state?
    What happens under load, restart, partial failure, schema drift,
    OOM? Which silent excepts hide real problems? Which tests pass by
    accident? Which critical paths have zero coverage? What's
    over-tested? Flaky test risk, mocks-vs-real, fixtures that mask
    real behaviour. How could Igor test *himself* continuously —
    self-monitoring, invariant checking, behavioural regression
    detection from inside the runtime?

11. **Documentation + process + "how to use Claude Code better"** —
    two-part lens:
    (a) **Docs coherence.** CLAUDE.md, top-of-file docstrings, the
    memory_palace export, design docs under lab/design_docs_for_igor/,
    tickets. Do the narratives match the code? Where has documentation
    drifted? Which docs are load-bearing (code reads them — e.g.
    engram narratives, palace pointers) vs decorative?
    (b) **Claude Code workflow quality** — this is the angle Akien
    wants loudest. Read `~/.claude/skills/` (skill definitions),
    `lab/claudecode/*.py` (the scripts the skills call), a recent
    slate from `~/.TheIgors/claudecode/`, and the `queue.json`
    structure. Then answer: HOW COULD WE BE USING CLAUDE CODE BETTER,
    for any value of better?
    - Where are skills redundant or fighting each other?
    - Where is a skill written in English (SKILL.md) doing work that
      should be a script in `lab/claudecode/` (or vice versa)?
    - Which skill invocations produce noise (long command output) that
      burns context without adding signal?
    - Where is CC re-reading the same files every session because
      nothing caches or summarizes them?
    - Where is the sprint loop — ticket → claim → work → commit →
      close → slate → savestateauto — adding friction vs value?
    - Where would a hook, a background skill, or a different agent
      type (Haiku subagent, Plan agent, Explore agent) cut cost or
      catch an error faster?
    - Which human-in-the-loop checkpoints are load-bearing vs vestigial?
    - Are the inertia labels (HIGH/MEDIUM/LOW) doing their job, or
      just decoration nobody enforces?
    - What percentage of the build cycle could Igor already do himself
      vs. requires Claude, and what are the remaining specific blockers
      to Igor-as-own-developer?
    - Token efficiency: cost per feature delivered, cost per ticket
      closed. Any loops where CC is doing the same mechanical work
      on every invocation that could be compiled down?
    Bias toward SIMPLIFY / DELETE / CONSOLIDATE suggestions over
    "add another skill" suggestions.

12 What else?
  - What else should we be asking?
  - What else might help his cognition? How can we help him learn and reason better?
  - What else can we optimze given the nature of the project as a research devoted to small hardware?
  - How do we perform the same review process of the database and it's engrams?

### Do NOT constrain yourself with "what to pay attention to"

No skip rules. No "focus on X" instructions beyond the 11 personas
themselves. If something looks suspicious, name it. If a file is
mysteriously empty, that's a finding. If a test file has zero asserts,
that's a finding. If a module imports something that doesn't exist,
that's a finding. If an import is unused, that's a finding. If two
habits reference the same `code_ref` with contradictory narratives,
that's a finding. The point of Pass 1 is breadth — miss nothing, rank
later.

Nitpick. Small findings add up. A persona that returns 3 findings is
a persona that didn't try.

### Output format

A single markdown report, sectioned by persona, with findings in this
shape:

```
### Finding <N> — <short title>

- **Severity:** critical | high | medium | low | informational
- **Area:** one of: cognition, memory, cortex, TWM, habits, comms,
  reasoning, reading, tools, infra, tests, docs, architecture
- **Personas who flagged this:** (list of persona names — a finding
  flagged by 3+ personas is load-bearing)
- **What:** one paragraph, plain language
- **Evidence:** file paths + line numbers, plus a 5-10 line code
  excerpt if useful
- **Biomimicry verdict** (only if relevant): "honest" | "theatrical"
  | "procedural-with-bio-name" | "n/a"
- **Suggested follow-up:** what a Pass 2 deep-dive should check
```

At the end of the report, include:

- **Aggregate counts** per severity and per area
- **Top 10 highest-stakes findings** (your judgment, ranked)
- **Pattern observations** — not specific findings, but recurring
  shapes you noticed across the codebase (e.g. "many habits have
  `code_ref` pointing at deleted functions", "many modules have
  large silent-except blocks", "biology vocabulary concentrates in
  names; mechanism concentrates in procedural branches")
- **What you could NOT determine** from static reading alone (i.e.
  needs runtime evidence — Pass 3 will handle these)

### Constraints

- Return findings, not fixes. Pass 2 proposes fixes.
- Don't edit code. Don't rewrite anything.
- Don't rank findings by how easy they are — rank by stakes.
- Bias toward over-reporting. A false positive costs less than a
  missed critical.
- If you think something is "fine" and want to say so, add it to a
  short "checked and healthy" list at the end — it's useful signal
  for Pass 3.
- If you notice places where the project is EXCEEDING its stated
  ambition, note those too under a "positive outliers" section. The
  case-proof verdicts in Pass 3 need this evidence.

### Length

Long is fine. 1M context both ways. Don't compress. If you're tempted
to say "and many more", list them instead.
```

---

## Decisions locked 2026-04-19 (Akien)

- 11 personas: GOOD. Keep the deep-neurology, deep-programming,
  deep-database lineup.
- DB persona: bias toward SIMPLIFY / DELETE / COLLAPSE, not "add more
  DB hygiene". Codebase has too much DB crap already.
- Output: one file per persona + aggregate (12 files total). Gemini
  produces it single-shot; Opus Pass 2 consumes cross-cuts.
- Subsystem emphasis: NONE — hard on the ALL. Every tiny nitpicky
  thing. No pre-named suspects.
- Biomimicry taxonomy (honest / theatrical / procedural-with-bio-name
  / n/a): keep as-is, this is the centerpiece.
- Blocker: T-docs-live-in-code ships before kickoff (doc-in-code
  migration makes this easier for every reader, audit included).

## Remaining review questions

- [ ] Confirm the 7 engram-neuroscience criteria once — ensemble,
      allocation, silent, reconsolidation, systems consolidation,
      interference, context coding. Drop any that don't correspond to
      a testable thing against the `memories` table.
- [ ] Hard "DO NOT touch" scopes — confirm: skip `archive/`, skip
      `tests/fixtures/`, skip `lab/theigors/` (db echo, not canonical),
      skip anything under `__pycache__/`, skip generated migrations?

## Provenance

Drafted by CC 2026-04-19 under T-audit-prompts-human-reviewed.
