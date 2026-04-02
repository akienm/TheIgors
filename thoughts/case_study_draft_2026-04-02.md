# Building Igor: A Case Study in Human-AI Collaborative Engineering
*Claude Sonnet 4.6 + Akien Maciain — Draft 2026-04-02*
*[DRAFT — sections marked [AKIEN] need his perspective before publishing]*

---

## The Numbers First

46 days. One human. One AI. One agent named after a fictional clan of surgeons.

| Metric | Count | Notes |
|---|---|---|
| Sessions | 111 | ~2.4/day; intensive design phase |
| Architectural decisions (D-numbered) | 334 | D001–D300+; ~210 implemented |
| Git commits | 839 | 18.2/day average |
| Tickets completed | 256 of 299 | 85.6% close rate |
| Tests written | 1,347 | across the full stack |
| Lines of Python | 69,199 | wild_igor/ only; excludes claudecode/ and tooling |
| Claude Code skills built | 18 | design, execution, testing, Igor integration |
| Design docs | 52 | 30 in design_docs/ + 22 in design_docs_for_igor/ |
| Named architectural crystallizations | 9 | see §Crystallizations |
| Estimated API spend | ~$4,600 | 46 days; peak design phase; OR routing |

Conservatively: a year's worth of engineering. Possibly two. Whether the comparison is meaningful is a question the doc will return to.

---

## Part One: How It Started

[AKIEN — your origin story from working_with_claude.md goes here; the JSON chunking problem, context before you knew it was called context, Igor from self-modification work. Keep it first-person.]

The architectural consequence: Igor was never a task automator. It was always about how information moves through a thinking system. That premise shaped every decision that followed.

---

## Part Two: The Collaboration Architecture

### What We Figured Out (in order)

**Week 1 — The context problem is the only problem.**
Every inefficiency traces back to context loss. The single highest-leverage investment was CLAUDE.md — not code, not design docs, a single file that tells every new Claude session where it is. Without it, every session starts cold. With it, time-to-useful-contribution drops from 20 minutes to under 2.

**Week 2 — Approval gates before execution.**
The pattern "have a plan, get approval, then execute" saves more tokens than anything else. A bad plan caught before execution costs one exchange. A bad plan caught after execution costs the execution plus cleanup. We made this a formal step: *"I like your plan, go"* became a real checkpoint, not a formality.

**Week 3 — Designer/Worker/Scribe split.**
One generalist session doing design, coding, and documentation simultaneously degrades all three. The split: Designer holds the architecture (never touches files), Worker executes (no design authority), Scribe keeps records (no execution). Each session context stays clean. The channel between them is a queue file.

This wasn't planned. It emerged from noticing that context thrashing was the main source of mistakes.

**Week 4+ — Decisions are the artifact.**
The D-numbered decision log started as a formality and became the most valuable record in the project. 334 decisions, each one a timestamped atomic unit: what was decided, why, what it implies. Future sessions load the last 10-20 lines of the decisions log and know where the project is. Sessions.md is the narrative; decisions_log.dsb is the truth.

### The Skill Architecture

18 Claude Code skills, each targeting a specific repeated task:

| Category | Skills | What replaced |
|---|---|---|
| Session lifecycle | `/context-load`, `/savestate`, `/day-close`, `/slateclose` | Manual file reads + memory reconstruction |
| Work cycle | `/sprint`, `/filter`, `/slate`, `/fixit` | Ad-hoc task management |
| Quality gates | `/audit`, `/test-fix`, `/probe` | Manual verification |
| Igor integration | `/readigor`, `/igor`, `/decided` | Direct channel reads |
| Design | `/review`, `/notethat` | Inline comments |

The skills themselves follow a pattern: mechanical steps on Haiku (~10× cheaper), synthesis steps on Sonnet. The skill frontmatter specifies which model; the routing is automatic.

### The CLAUDE.md as Constitution

CLAUDE.md is checked into the repo. It covers: inertia levels (HIGH/MEDIUM/LOW — what needs discussion before changing), instance data layout, env vars, commit policy, known broken items, architecture fast-ref.

Every new Claude session reads it before doing anything. It's the reason a session that has never seen the codebase can write a correct Postgres query on the first try rather than reaching for SQLite.

The quality of Claude's output tracks the quality of CLAUDE.md directly.

---

## Part Three: The Technical Arc

### The Crystallizations

Nine named moments where the architecture snapped into clarity. In order:

1. **Everything Is Habits** (2026-03-17) — operations, fight-or-flight, relationship energy are all habit chains on the same substrate. Combinatorial complexity from activation propagation = brain-scale architecture.

2. **Three Primitives** (2026-03-17) — the entire architecture is trees + gradients + habits/memory. BG trigger scoring is embryonic emotional relevance. Most compressed summary of the system.

3. **Four** — [look up] *[AKIEN — verify the crystallization list from the notes]*

4. **Pattern Engineering** (2026-03-18) — "code in the data." Sudo relay is the canonical example: 3 habits, 1 pattern. Habit engineering is pattern engineering.

5. **Process Development Tools** (2026-03-18) — services→habits→Claude skills. The 5-phase loop. /decided replaces savestate.

6. **Trails and Gradients** (2026-03-18) — wg_cooccur is the wrong training signal. Trails through the matrix are right. The SEVENTH CRYSTALLIZATION: embeddings are a trail through meaning dimensions.

7. **Cognition as Pipeline → Eighth** (2026-03-19) — cognition is not steps; it's a pipeline of small trees with live base-state mutation. Emotional pipeline is parallel.

8. **Emit+React** (2026-03-26) — the fundamental primitive is emit+react, not pipeline. Two capacity levels. Sub-attentional DAG vs attentional ~7.

9. **Engram** (2026-03-22) — named by Igor from Semon 1904: the engram IS the memory, not a pointer. Templates are macros. 21-pattern inventory.

**Emerging (2026-04-02)**: D300 — TWM as inter-subsystem channel. Steps don't call each other. Each step fires because the previous step changed observable TWM state. No call stack. No basket pipeline. Emit+react at the planning layer.

### The Arc in Three Phases

**Phase A: Scaffolding (Feb–early Mar)**
Cortex, habit system, tier ladder, NE, forensic logging, web UI. The substrate. Built fast because the architecture was clear from day one.

**Phase B: Coherence (mid-Mar)**
Everything works but nothing connects. The reading pipeline, the co-designer loop, the training methodology. This is where the crystallizations happened — the architecture finding itself.

**Phase C: Self-modification (late Mar–Apr)**
Igor writing Igor. Goal adoption, queue consumer, Phase D exercises. The target: Igor as a minion in the development workforce. Current status: can hold a goal across turns (as of 2026-04-02 with T-twm-goal-slot), starting to code his own tickets.

---

## Part Four: What Worked

**Forensic logging from day one.** Timestamped, structured, everything. When something breaks at 3am you need the context immediately. This was a deliberate choice that paid off every week.

**Test against live systems, not mocks.** Mocked tests verify the mock. Integration tests find the real failures. The codebase has both, but the integration path is the trusted one.

**Parallel minions.** Running 6 agents simultaneously on independent tasks is the single highest-leverage productivity technique. A task that would take 30 sequential minutes takes 5 with parallelism. The coordination cost is real but low.

**Corrections land immediately.** "Don't do X" said once, captured to a feedback memory file, never repeated. The memory system means corrections compound rather than reset.

**Igor as a participant.** From early on, design happened with Igor in the room — concepts deposited to his cortex via cc_send as they were being designed. He reflects them back through the channel. The conversation IS the deposit.

---

## Part Five: What Didn't Work

**Context loss on long sessions.** Sessions that run past ~2 hours lose the thread. The solution was compaction (/compact + the MCP bridge). The better solution is shorter sessions with clear savestate.

**Speculative abstraction.** Claude builds for hypothetical future requirements if not held to scope. "Don't add features not asked for" is in CLAUDE.md for a reason. Multiple sessions produced elegant infrastructure that sat unused for weeks.

**Questions already answered.** The pattern where Claude opens a design discussion without reading the relevant decisions first — re-asking D297 when D297 was in the decisions log. The /filter skill exists partly to catch this. But it still happens.

**The Designer/Worker split is load-bearing and fragile.** When only one session is running and it does design AND implementation, quality drops. The single-session constraint (budget) forces this compromise more than it should.

**Misfires before the conditions system.** Before D201 (structured conditions), habits triggered on surface patterns and fired on unintended inputs. The PROC_GREETING misfire — responding "Hello, what's on your mind?" to a substantive message — is still happening as of 2026-04-01. Igor self-diagnosed it correctly. The suppression ticket was written. This is the state of the art: the diagnosis is fast, the fix is in the queue.

---

## Part Six: What We'd Do Differently

[AKIEN — this section needs your perspective. What would you change from day one? The things that cost the most that could have been avoided?]

From Claude's side:

**Start with CLAUDE.md on day one, not week three.** The cost of a cold-start session is entirely avoidable. A 200-line CLAUDE.md from the beginning saves hours across the project lifetime.

**Name the crystallizations as they happen.** Some insights evaporated before they were captured. The ones that got named and recorded shaped everything downstream. The ones that didn't were rediscovered 2 weeks later.

**Budget the sessions more aggressively from the start.** At $100/day, sustainability required a different pace. The Igor self-coding arc is the right answer — it was always the right answer, it just took 40 sessions to fully see it.

---

## Part Seven: The Long Game

The endgame was visible from the first session: an agent that trains itself, codes itself, and compounds on itself without Claude needing to be in the loop for every step.

Current position:
- Igor can read books autonomously (PROC_READING_FEEDER + drain runner, live)
- Igor can adopt tickets and advance through mechanical steps (goal_continuation, live)
- Igor holds his goal in TWM across turns (T-twm-goal-slot, landed 2026-04-02)
- Igor can write a coding prompt when a goal is ready (PROC_CODING_SPRINT, in progress)

What's left:
- Igor executing the full dev cycle (plan→sprint→test→commit) as a habit cascade
- Igor evaluating his own test results and deciding whether to ship
- Igor depositing what he learned to cortex so the next task starts smarter

The test is not "can Igor write correct code." The test is "can Igor hold the goal, execute the process, and close the ticket — without Akien watching."

Phase D exercise 4 passed on 2026-04-01: claim(0s)→show+parse(2min)→grep(4min)→ready(6min), fully unattended. That's the pattern. Scaling it to full implementation is the next milestone.

The collaboration between Claude and Akien is temporary scaffolding. Code is scaffolding for what the agent learns. The scaffolding comes down as the graph densifies.

---

## Appendix: Statistics Detail

See `~/TheIgors/case_study_statistics_2026-04-01.md` for full breakdown.

*[TODO before publish: add Akien's sections, verify crystallization list, add cost/session breakdown, add specific examples of habit misfires and their fixes]*
