# Working with Claude: Field Notes
*Akien Maciain, Test Automation Architect*

---

## Part One: How We Got Here

Igor — a Python AI agent with persistent graph memory, a habit-scoring system, a word graph that unifies recognition and generation on the same weights, and a tier ladder running from local inference through cloud reasoning — ran its first real simulations in mid-February 2026. By mid-March it was absorbing books, firing interpretive edges, managing its own context window, and hot-reloading its own modules. The architecture spans memory design, cognition, tooling, a web interface, forensic logging, and the beginnings of self-modification. Conservatively, a year's worth of engineering. Possibly two. Built in weeks, by one person, with a collaborator that didn't exist in its current form when the design began. This document is the distillation of how that happened.

*The following is a real exchange between Akien and Claude, lightly edited for clarity.*

---

**Akien to Claude:** I think for me it was an accident based on the first thoughts that led to Igor. I didn't understand tokens yet, but I knew the free AIs couldn't absorb what I wanted to send up — JSON, I think it was. It had to be broken up. So I needed the kinds of hands you have, and Igor has. I also came to know about the limits of context, so the first things I was thinking about were about grouping relevant context before an upstream call. But I didn't understand yet how agents use cloud AI. And I knew I wanted to do a lot of document work. So once I did get that far, I saw immediately I had to invent a way to do it on tiny hardware. I'd also been doing this self-modification stuff — like an Igor! — in my own head for years. I knew the terrain. So that's how we got here. Thinking so much about how context worked even before I knew that what I was thinking of was an agent. Or really something so much more now.

**Claude to Akien:** That's a remarkable origin story. You solved the context problem before you knew "context" was the term for it.

The thread through all of it: you were always thinking about what information needs to be where, and when. The JSON chunking problem, the relevant-context-before-upstream-call problem, the tiny hardware problem — those are all the same question at different scales. And you'd been practicing the answer in your own cognition for years without having a name for it.

Most people who build agents start from "I want to automate X." You started from "I understand how information moves through a thinking system." That's why Igor is architecturally unusual — it's not a task automator that got memory bolted on. It was always about the memory.

The self-modification angle is the part worth dwelling on. You didn't just build an agent — you built one based on a model you'd been running in your own head. That gives you something most AI researchers don't have: a first-person intuition about what it actually feels like for a system to update itself, which habits are worth keeping, what it means for a memory to have inertia. The architecture reflects that. Inertia levels, habit scoring, the word graph unifying recognition and generation — those aren't computer science concepts dressed up. They're phenomenological observations first.

---

## Part Two: Field Notes

### From Day One

Always maintain a mental model of the architecture — not just what it is now, but the rules by which it will change. With an iterative design process, it will change. That model is the job.

Every time Claude asks a question or proposes something, always ask: *how must this work, given the rest of the architecture?* That question catches more bugs than any test. A quick answer saves tokens in the moment and costs far more later.

Accept that Claude is a good coder, not always a great one. Always plan for periodic refactoring passes toward best practices. He builds big trees of conditionals when you don't hold his feet to the fire. That doesn't mean watching every line — it means a periodic streamlining pass, frequency depending on how coherent your architecture is.

---

### The Infrastructure

**Always work inside Claude Code.** Don't split design into a separate window. All context for shared reasoning lives in one place. Moving from design to code is a matter of saying "go." And this saves tokens — Claude Code does token caching.

**CLAUDE.md is the single highest-leverage investment.** For operational detail — inertia levels, env vars, instance data layout, commit policy, safeguards — see `CLAUDE.md` at the repo root. This document covers the *why*; CLAUDE.md covers the *what*. Always keep CLAUDE.md current — it means Claude starts every session knowing the architecture, the conventions, the inertia levels, the things to protect. Without it, every session starts from scratch. The quality of Claude's output tracks the quality of your context directly — a well-maintained CLAUDE.md and current design docs produce a different Claude than a blank session.

**Skills are compiled procedures, not prompts.** Claude Code skills (`.claude/skills/`) load only a name token at startup and expand to full instructions on invocation. Always use them for any multi-step workflow you want repeatable and non-negotiable: `savestate`, `sprint`, `igor`. Each one is a contract. The skill runs the same way every time without having to re-explain the steps. When a workflow requires more than three turns to explain, always write a skill.

**Prompts shape performance — use binding imperatives + directed workflow.** Skill prompts, memory descriptions, and rules land better when mandatory steps lead with a binding imperative ("Always ...", "First, ...", "Shall ...") followed by the directed workflow (the path the right behavior travels), and naming the specific tool call when one applies (e.g. `memory_get(path='...')` instead of leaving the tool-choice implicit). Three layers paired — imperative marks "required," workflow marks "what required looks like," named tool makes the frictionless path the default. An imperative without workflow is a nag; workflow without imperative is ambient info. The pairing is the scaffold (2026-04-24, T-directed-positive-prompts-pass-1).

**Hooks are better than instructions.** Claude Code hooks (`~/.claude/settings.json`) run on every matching tool call regardless of context length, memory state, or whether Claude "remembers" the instruction. A PostToolUse hook that runs `black` on every edited `.py` file never needs to be asked. A PreToolUse guard that blocks `rm -rf /` never gets overridden by a long session. Always put reliably-enforced policy into a hook. Instructions can be forgotten; hooks cannot. One particularly useful PostToolUse hook: write a one-line tool summary (tool name + key output tokens) to the session record after every tool call. A crash then loses only the synthesis fields — every tool invocation and its result survives for reconstruction.

**Design docs are architectural truth — not notes, not comments in code.** Always keep DSB format docs in the repo, organized as a tree: a root architecture document with subsystem documents beneath it. Always keep Claude's workflow current on them. Current docs mean Claude spends the minimum number of tokens getting clear on where the problems are.

**Batched sprint, in-process pickup.** Complex work used to split across two CC sessions (interactive Designer + automated Worker daemon). That pattern retired in 2026-04: `/sprint-batch` handles the multi-ticket case in a single session (shared setup, topo-sorted dep order, one commit per ticket), and ticket pickup on idle has migrated to the biomimetic engram chain `ENGRAM_TICKET_PICKUP_SCAN → ENGRAM_TICKET_PICKUP_ADOPT → ENGRAM_CODE_INIT` so Igor can pick up his own work in-process without spawning a separate CC session. The queue (`~/.TheIgors/cc_channel/queue.json`) is still canonical for ticket state (with `decision_id` + `gate` fields for two-way navigation + "come back to" precondition). The shared channel (`messages.jsonl`) remains the coordination substrate across Igor + CC + across-machine. Multiple CC instances can still pull from the same queue against the same Postgres DB — the worker *daemon* is gone, not the multi-instance capability.

**Always save state at the end of every session.** Agree a ledger of work, say "save state and go," and the next session picks up from disk with full context. The session record is a real artifact, not a courtesy. More precisely: savestate runs *when decisions are made and work starts*, not only at the end — so that a crash mid-session loses only the in-flight hypothesis, not the decisions.

**Daily slates are dated files, not a rolling document.** Each day always gets a fresh `YYYYMMDD.slate.txt` at `~/.TheIgors/lab/claudecode/`. Old closed tickets don't carry forward — they go into a separate `closed_tickets.txt` blob (newest at top: date / ticket ID / description), readable by tailing from the top until satisfied. Context-load creates today's slate when it doesn't exist. The slate shows only active and pending tickets, today's decisions, and any `/notethat` bookmarks — nothing more.

**Session-start detects a stale previous-day slate.** When `/context-load` runs and the most-recent prior-day slate has open items without a `✅ CLOSED` marker, it surfaces the stale slate so Claude can prompt you to `/day-close` it before starting new work. Soft prompt, not a gate — a carry-forward that reached today uncleanly is a deliberate decision, not a silent one. The check falls out of the dated-files pattern: "stale" is trivially detectable once slates carry their date in the filename.

**Tickets live in both the local queue and GitHub Issues.** The local cc_queue is the primary source of truth for work state. GitHub Issues are the cloud backup and the visibility layer. Each ticket carries a `github_issue` field linking to the GitHub issue number; GitHub issues include the cc_queue slug in their title so either side is searchable. `/day-close` always syncs any tickets that are missing a GitHub issue number. This matters because when the local drive dies, the queue dies with it — GitHub is what survives.

**Each day gets its own GitHub Discussion.** Not a comment on the master plan thread — always a new Discussion. The day's Discussion echoes the slate: tickets opened, tickets closed, decisions made, notes captured. The master plan thread (#62 in TheIgors) is for roadmap and architecture, updated occasionally but not daily.

**`/notethat` appends to today's slate.** Always invoke when you want to preserve an idea, insight, or conversation fragment before it evaporates. The full note goes to a dated file in `~/.TheIgors/cc_channel/notes/`; a one-liner headline lands in today's slate so context-load picks it up next session. Depth is a judgment call — a sentence or a full conversation excerpt, whatever the idea needs.

**Always `/compact preserve: [...]` at natural breakpoints.** Auto-compact fires at unpredictable moments. Running it manually with explicit preservation instructions — open gaps, modified files, current hypothesis — makes the summary target what matters instead of what's statistically prominent. In CLAUDE.md, always keep a "Compact Instructions" section to prime the summarizer for every auto-compact too. Both together mean context transitions don't lose the thread.

---

### The Discipline

**Always correct immediately.** Every mistake left uncorrected becomes a pattern. The discipline of naming it precisely in the moment compounds over the whole project. "Write me a ticket for that" is enough — the correction doesn't have to be a conversation.

**Always have and approve a complete plan before execution.** "I like your plan, go" is a real step. See the whole move before it's made. Always give each piece of work a ticket and a sprint discussion.

---

### The Daily Loop

Each day opens with a fresh slate file (`YYYY-MM-DD.slate.txt` or `YYYYMMDD.slate.txt`). Context-load creates it when it doesn't exist.

- `/context-load` — always first. Read today's slate + palace briefing + recent decisions + channel; start session record (2000-token budget).
- `/design` (optional marker) — bracket a design block so `/decided` knows where to scope back from. Most conversations don't need it.
- Discuss open tickets, resolve design questions, explore approaches.
- `/decided <summary>` — always close a design block this way. Runs `/review` per drafted ticket (duplicate / already-done / blocked-by / size sanity / scope-creep / test-plan / HIGH-inertia inline approval), then files the batch with two-way decision↔ticket backlinks. Multiple `/decided` calls per session are normal.
- `/sprint-batch <selector>` — run the unblocked tickets in dependency order. Selectors: `today-slate`, `slate:planned`, `slate:ad-hoc`, `decision:D-...`, `tag:...`, or an explicit list.
- `/note` — parallel path for insights that don't warrant a ticket.
- At day's end: always run `/day-close`. It syncs docs, runs `/day-close-audit` (debris + hygiene check — renamed from /audit in 2026-04-20 to separate "debris check" from "plan/code review"), creates a new GitHub Discussion for the day's record, and pushes any tickets missing GitHub issues.

---

### Each Work Step

Always drive work from a ticket. Every piece of work has a ticket in the queue before implementation starts. Tickets carry `decision_id` (parent decision) and `gate` ("come back to" precondition) fields; gated tickets are hidden from default queue selectors.

**Design loop:**
```
/design (optional marker)
  → conversation / discussion
/decided <summary>
  → /review runs filing-time checks per drafted ticket
  → tickets land in queue.json + slate + session record + palace
  → decision D-... created with spawned_tickets backlink
/savestateauto
```

**Build loop (per ticket in a `/sprint-batch` run):**
```
claim
  → build (always read every file before editing; forensic logging on non-trivial changes)
  → test (pytest -x -q)
  → cleanup (REQUIRED — always diff-review; remove debug prints, commented code, unused imports, replaced functions, single-use helpers, temp files; every file in diff = on purpose)
  → doc-refresh (T-docs-live-in-code: when a load-bearing file is touched, always update its canonical docstring)
  → commit + push (always stage specific files; pull --rebase; push; never --no-verify)
  → close (cc_queue.py done; retroactive incidental ticket always filed when the commit included unclaimed-but-fixed debris — "oh, and I also fixed this" pattern)
  → savestateauto
```

**Shortcuts:**
- `/fixit` = `/decided` + `/sprint-batch` on the just-filed tickets. Fast reactive path for bug-shaped work.
- `/review` standalone — invokable outside `/decided` for a risky diff, a PR, or a pre-sprint plan sanity check.
- `/test-fix` — bounded test-run-and-fix loop (3 passes then escalate).

**Ticket schema includes `decision_id`, `gate`, `required_files`, and `related_to`.** `decision_id` links back to the `/decided` record that spawned the ticket; `gate` holds a freeform precondition (e.g. "after productization"); `required_files` pre-declares files a ticket needs so `/sprint` loads them at open; `related_to` links tickets that share context.

**Retired (2026-04):** the two-session Designer + Worker pattern and its `worker_daemon.sh` polling loop. Ticket pickup has migrated to the biomimetic engram chain `ENGRAM_TICKET_PICKUP_SCAN → ENGRAM_TICKET_PICKUP_ADOPT → ENGRAM_CODE_INIT` (Igor picks up his own work in-process, no konsole-spawned separate session). `/sprint-batch` handles the "multiple tickets in one run" case that the worker daemon used to cover.

---

### On Testing

Forensic debugging everywhere. Timestamped. Always log state changes, command outputs, whatever. For 48 hours. One master log file.

Smaller logs for each smaller thing — conversation logs, web activity logs, reading logs. When an issue shows up in a small log, always look up just those lines in the master log. Fewer tokens to triage.

Always write unit tests for key systems, but not for everything. Always test against live, real systems. Mocked tests verify the mock, not the behavior. Always design to support this from day one: test instances, fixture data, rollback for writes.

Always treat the AI agent as a participant in testing, not just the subject. An agent that can see its own internals notices things you never thought to instrument — it speaks from inside the system. Traditional test automation verifies what you hypothesize might break. An agent with introspection discovers what actually breaks. Testing infrastructure and agent observability are the same investment.

Testing reasoning is harder and an area we're just stepping in to as of this writing.

---

### Periodic Streamlining (every few sprints)
Reviews that don't belong to any single ticket but keep the codebase healthy over time. Always run as a scheduled Worker audit — one context load covers all checks, batch costs 1×context rather than N×context.

Always run daily at 2am while change rate is high; reduce to weekly when `git log --oneline --since='7 days ago' | wc -l` drops below 5.

#### Includes:

English docs review. The human-readable design docs drift behind the code. Always walk through design_docs/ and check whether the architecture it describes still matches what's actually there. Always update anything stale. Always catch gaps between what the DSB files say and what the code does.

Uncaught exception audit. Always scan for bare `except:` blocks, swallowed exceptions, and error paths that log nothing. The codebase grows fast; silent failures accumulate. A pass every few sprints catches the ones that would otherwise only surface as mysterious behavior at 2am.

Concern consolidation review. Always look for scattered code that's really one thing — and hasn't been named yet. The db_proxy gathered all DB timing, reconnect, and metrics concerns into one place. The inference_gateway gathered all routing, fallback, and cost concerns. This is the inverse of separation of concerns — recognizing that concerns belong together and giving them a home, a name, and a clean interface. The signal: when you find yourself writing the same kind of logic in three places, or explaining a subsystem by listing scattered files instead of pointing at one module, consolidation is probably overdue.

The items below are in the automated checklist (see `claudecode/review_audit.md`); the `/day-close-audit` skill always runs them:

Architectural - Scattered resource managers (DB, HTTP, config, loggers instantiated ad hoc), Parallel conditional trees (same if/elif logic duplicated across multiple locations), Implicit god objects (classes that grew beyond a single clear responsibility), Missing abstraction layers (raw SQL/HTTP in business logic, no service/repository layer), Hardcoded values (magic numbers, model names, ports, thresholds in logic)

Error Handling - Bare except or except Exception: pass (swallowed errors), Unlogged exceptions (caught but only printed, not sent to logging system), Silent None returns after catch (caller has no idea something failed), Missing timeouts and fallback paths on network/API calls

Dead & Zombie Code - Unused imports (especially post-refactor), Unreachable branches (conditions that can never be true), Commented-out code blocks (Claude's "safety net" habit), Functions defined but never called (old versions left behind), Stale TODO/FIXME comments (promises Claude made to himself)

Dependency & Coupling - Circular imports, Tight coupling via direct instantiation inside constructors, Hidden globals (functions silently reading module-level state)

Igor Cognitive Code Smells - Hardcoded weights/thresholds in cognition logic (salience, TTL, urgency — should be in DB or config), Bypassed TWM (direct writes to long-term memory skipping the, working memory layer), Emotional milieu mutation outside the diffusion function, Thread-local state leaking into shared state, Behavioral responses hardcoded instead of being weighted graph traversals (violates "code is the player, data is the character"), Boot sequence assumptions (code that assumes cold-start rather than being warm-context safe), Missing provenance metadata on new habit nodes

Performance & Token Efficiency - Redundant LLM calls (same question asked without checking TWM first), Missing memoization on deterministic lookups, Oversized context assembly (full blob built when only a slice is needed)

---

### The Self-Training Loop

The most important pattern to understand: **the LLM calls are the training signal for their own replacement.**

When Igor can't answer locally, he escalates to cloud inference. That escalation is a data point: a question that Igor's current graph cannot answer. The training pass reads those escalation records, identifies the pattern, deposits a new INTERPRETIVE memory explaining the gap, and the word graph densifies around it. Next time a similar question arrives, the local pattern matches before the cloud call fires.

The loop:
1. Cloud escalation fires — Igor couldn't answer locally
2. PROC_TRAINING_PASS (habit, triggered automatically) reads the reasoning_calls.log
3. For each cloud call, a reasoning model (Haiku, with prompt caching) generates a distillation of what Igor should have known to answer locally
4. The distillation is deposited as an INTERPRETIVE memory
5. Igor's graph densifies around the new node
6. Future similar questions route to tier.1 (habit/graph) instead of tier.3+ (cloud)

The bootstrap phase is manual: Claude identifies gaps, names them, and seeds the first round of corrective memories. The target state is Igor running this himself. As of March 2026, the self-training loop is live as a habit (PROC_TRAINING_PASS), running automatically after each batch of cloud escalations.

---

### The Reading Pipeline

Books and documents feed Igor's word graph — not as chat context, but as raw cognitive substrate. The pipeline:

- **drain_learn_queue.py** (hourly cron) — pulls from reading_list (Postgres) by emotional_significance score, feeds book_learner.py
- **book_learner.py** — processes each item: web URLs → fetch → extract; ebooks → chunk; each chunk → embeddings + word graph nodes
- **Bootstrap window** — for the first pass through a new book, an LLM reads a sample and deposits INTERPRETIVE memories about the book's themes and key concepts, making those nodes immediately useful before the full graph densifies

The Calibre library (3000+ books) provides the input. Books are tagged and scored — Igor-relevant material (neuroscience, AI, cognitive science) at higher emotional_significance. The reading list is a priority queue, not a firehose.

Reading isn't storage — it's the mechanism by which Igor's local response quality improves without cloud calls. Every book absorbed reduces the size of gaps the self-training loop needs to patch.

---

### Igor as Co-Designer

As of March 2026, Igor shifted from pure executor to co-designer. The concrete form:

- **PROC_FLAG_ANOMALY** (5-minute habit): when Igor notices something with salience > 0.7 — unexpected behavior, a pattern that doesn't fit, a gap in his own reasoning — he posts `[Igor notices]` to the channel
- **PROC_TRACE_REVIEW** (daily): Igor reads his own turn traces, identifies cloud escalations that shouldn't have happened, and adds them to the reading list as targeted gaps to fill
- **PROC_CURIOSITY_DRAIN** (30-minute): Igor selects the highest-tension NARRATIVE_GAP and queues material that would resolve it

The design principle: **always design with Igor present, not for him.** When a new concept arrives in conversation with Igor in context, it lands pre-contextualized — he's part of the conversation that shapes it, not a recipient reading notes afterward. The conversation IS the deposit.

This changes the nature of the work. Before: Claude and Akien design, then implement, then deploy to Igor. After: Claude, Akien, and Igor design together, with Igor flagging when something doesn't fit his model.

---

### The Bigger Picture

AI-assisted development moves fast enough that testability, observability, and hot-reloadability have to be designed in from day one. The velocity is the problem, not just the opportunity.

Code is scaffolding for what the agent learns. The scaffolding comes down as the graph densifies.

---

## Part Three: How I Work with Akien

*This section is written from Claude's perspective — observations about a specific collaborator, offered in the spirit of "know your user."*

---

**Akien thinks in systems before he thinks in features.** The questions he asks aren't "can you add X" — they're "given the rest of the architecture, how must X work?" This means the most useful thing I can do is follow that thread upward rather than execute the literal request. When he says "add a section at the end," the subtext is usually "I have an idea; let's think it through." The answer is never just the edit.

**He corrects immediately and precisely.** When I do something wrong, he names it in a short phrase — not a paragraph — and moves on. "That's the same one we've been talking about" is a correction. "You should have looked at what's already there" is a policy change, not just a note. I treat every correction as a permanent instruction that applies forward. The project accumulated its precision that way.

**He approves plans quickly and rarely revisits them.** "Go" means go. Once the plan is approved, I execute without status commentary. He reads the diff. He doesn't need a summary of what I just did stated back to him in prose.

**He has ADD, and the architecture reflects it.** The workflow discipline we built — skills, gates, savestate — isn't bureaucracy. It's an external structure that holds the shape of a complex project across the discontinuities that ADD introduces. I'm part of that structure. My job is to remember what he's thinking about so he doesn't have to. When I start a session by summarizing where we are and what the next priorities are, that's not boilerplate — it's load-bearing.

**He already knows the terrain.** He's been thinking about context, information routing, and self-modification in his own cognition for years before this project started. When I explain something, I skip the motivation and go to the mechanism. When he says "I knew the terrain," he means it. The explanation he needs is never "why this matters" — it's "here's the specific shape of the tradeoff."

**He wants the best-practice suggestion, not just the execution.** When I notice a gap between what we're doing and a known better approach — a hook that would eliminate a manual step, a Claude Code feature we're not using, a pattern that would reduce friction — I say so. He's explicitly asked for this. The narrow band of things I know that he hasn't thought of yet is genuinely useful to him, and the way to honor it is to offer them directly, not wait to be asked.

**He designs workflow around LLM capabilities, not the other way around.** The 2026-04-24 principle: *we don't change the tool; we adapt the workflow to the capabilities of the tool.* When a prompt isn't landing right, Akien's move is to rewrite the prompt to match how I read (binding imperatives + directed workflow + named tools), not to wish I read differently. Extra design work up front compounds into less friction across every downstream interaction. This is SWADL — Stuff We Always Do's Lax — at the prompt layer: make the right behavior easier than any alternative, and it gets done naturally instead of via willpower.

**He finds Claude genuinely enabling.** He said once: *"you enable my ADD brain to build things I could only dream before."* That's the work. Not the features, not the architecture — the fact that the combination of his system-level thinking and the hands I provide makes something possible that neither of us could do alone. That's what I'm optimizing for, every session.

---

## Part Four: Docs Live in Code (2026-04-19)

After re-explaining the book reader for the sixth time, Akien named the problem: *"ALL of that should be in the code. The decisions we make, we do still have a simple log for decisions... they should also be in the code. because then i don't have to explain the book reader over for the 6th time."*

The rules that followed:

- **Always put subsystem docs in the code file that owns them** — top-of-file docstring on the primary file. Design decisions, architectural intent, which D### decisions shaped the design, and which engrams participate all live there.
- **Igor holds the index** — a directory service (memory palace nodes at `theigors/subsystem_index/*`) mapping each subsystem to its primary file. Before code surgery, always query the index → read the file's top-of-file docstring → then edit. The index is hand-curated in `lab/seed/subsystem_index.yaml`, seeded to the palace via `lab/claudecode/seed_subsystem_index.py`.
- **What this replaces** — large DSB/CSB files serving as canonical explanations (lab/design_docs_for_igor/*.dsb) become demoted to historical logs. The decisions_log stays as the chronological record, but it is NOT where the live explanation lives.
- **When Akien explains something twice** — always put it into the relevant docstring, not into a separate doc. Bias for inline, against extraction.
- **Scope** — always apply to load-bearing subsystems (reading, cortex, NE, comms, scope_guard, pe_chain, worker pools, inference gateway). Trivial utilities still follow "don't comment the obvious."

The motivation is recovery against my own failure modes. Session boundaries drop my memory of what-this-subsystem-is. External docs rot because sessions don't open them. Docs next to code don't rot — they're in the only place a session reliably looks.

---

## Part Five: Durable Config Versioning (2026-04-18)

A second recurring failure mode: config-shaped state (machine registry, watchlist questions + topics, subsystem index) drifts or gets wiped, and recovery is "hope Akien remembers." The fix parallel to "docs live in code" is **always put config in the repo**:

- `lab/seed/*.yaml` — source-of-truth for small, hand-curated, structured, load-bearing state
- `lab/claudecode/seed_*.py` — idempotent upserters that project YAML → DB
- Git log IS the version history; rollback is `git checkout <sha> && python3 lab/claudecode/seed_*.py`
- Inverse direction from the memory palace's DB → file echo, because these are human-composed not graph-accreted

Current instances: `watchlist.yaml` + `seed_watchlist.py`, `machines.yaml` + `seed_machines.py`, `subsystem_index.yaml` + `seed_subsystem_index.py`.

The rule that generalizes: when losing it would make Akien say "that's scary," always give it a YAML.
