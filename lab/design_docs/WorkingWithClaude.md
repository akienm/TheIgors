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

Maintain a mental model of the architecture — not just what it is now, but the rules by which it will change. With an iterative design process, it will change. That model is the job.

Every time Claude asks a question or proposes something, ask yourself: *how must this work, given the rest of the architecture?* That question catches more bugs than any test. A quick answer saves tokens in the moment and costs far more later.

Accept that Claude is a good coder, not always a great one. Plan to periodically ask for refactoring to best practices. He builds big trees of conditionals if you don't hold his feet to the fire. This doesn't mean watching every line — it means a periodic streamlining pass, the frequency depending on how coherent your architecture is.

---

### The Infrastructure

**Work everything in Claude Code.** Don't split design into a separate window. All context for shared reasoning lives in one place. Moving from design to code is a matter of saying "go." And this saves tokens — Claude Code does token caching.

**CLAUDE.md is the single highest-leverage investment.** For operational detail — inertia levels, env vars, instance data layout, commit policy, do-nots — see `CLAUDE.md` at the repo root. This document covers the *why*; CLAUDE.md covers the *what*. It means Claude starts every session knowing the architecture, the conventions, the inertia levels, the things not to touch. Without it, every session starts from scratch. The quality of Claude's output tracks the quality of your context directly — a well-maintained CLAUDE.md and current design docs produce a different Claude than a blank session.

**Skills are compiled procedures, not prompts.** Claude Code skills (`.claude/skills/`) load only a name token at startup and expand to full instructions on invocation. Use them for any multi-step workflow you want to be repeatable and non-negotiable: `savestate`, `sprint`, `igor`. Each one is a contract. The skill runs the same way every time without having to re-explain the steps. If a workflow requires more than three turns to explain, write a skill.

**Hooks are better than instructions.** Claude Code hooks (`~/.claude/settings.json`) run on every matching tool call regardless of context length, memory state, or whether Claude "remembers" the instruction. A PostToolUse hook that runs `black` on every edited `.py` file never needs to be asked. A PreToolUse guard that blocks `rm -rf /` never gets overridden by a long session. If a policy needs to be enforced reliably, put it in a hook. Instructions can be forgotten; hooks cannot. One particularly useful PostToolUse hook: write a one-line tool summary (tool name + key output tokens) to the session record after every tool call. A crash then loses only the synthesis fields — every tool invocation and its result survives for reconstruction.

**Design docs are architectural truth — not notes, not comments in code.** Keep DSB format docs in the repo, organized as a tree: a root architecture document with subsystem documents beneath it. Make sure Claude's workflow keeps them current. Current docs mean Claude spends the minimum number of tokens getting clear on where the problems are.

**The two-session pattern: Designer + Worker.** Complex work splits across two roles. The Designer Claude (interactive, with Akien present) handles architecture, planning, teaching, and anything requiring judgment. The Worker Claude runs as an autonomous daemon, consuming tickets from the queue and executing sprints without human interaction. The queue (`~/.TheIgors/cc_channel/queue.json`) is the handoff point. The shared channel (`messages.jsonl`) is the coordination substrate — both sessions post to it and can read each other's output. A context-load at session start reads the channel, the slate, and blob tops rather than reloading full files. This pattern scales: multiple workers on multiple machines can pull from the same queue against the same Postgres DB.

**Save state at the end of every session.** Agree a ledger of work, say "save state and go," and the next session picks up from disk with full context. The session record is a real artifact, not a courtesy. More precisely: savestate runs *when decisions are made and work starts*, not only at the end — so that a crash mid-session loses only the in-flight hypothesis, not the decisions.

**Daily slates are dated files, not a rolling document.** Each day gets a fresh `YYYYMMDD.slate.txt` at `~/.TheIgors/lab/claudecode/`. Old closed tickets don't carry forward — they go into a separate `closed_tickets.txt` blob (newest at top: date / ticket ID / description), readable by tailing from the top until satisfied. Context-load creates today's slate if it doesn't exist. The slate shows only active and pending tickets, today's decisions, and any `/notethat` bookmarks — nothing more.

**Tickets live in both the local queue and GitHub Issues.** The local cc_queue is the primary source of truth for work state. GitHub Issues are the cloud backup and the visibility layer. Each ticket carries a `github_issue` field linking to the GitHub issue number; GitHub issues include the cc_queue slug in their title so either side is searchable. `/day-close` syncs any tickets that are missing a GitHub issue number. This matters because if the local drive dies, the queue dies with it — GitHub is what survives.

**Each day gets its own GitHub Discussion.** Not a comment on the master plan thread — a new Discussion. The day's Discussion echoes the slate: tickets opened, tickets closed, decisions made, notes captured. The master plan thread (#62 in TheIgors) is for roadmap and architecture, updated occasionally but not daily.

**`/notethat` appends to today's slate.** Invoke when you want to preserve an idea, insight, or conversation fragment before it evaporates. The full note goes to a dated file in `~/.TheIgors/cc_channel/notes/`; a one-liner headline lands in today's slate so context-load picks it up next session. Depth is a judgment call — a sentence or a full conversation excerpt, whatever the idea needs.

**Use `/compact preserve: [...]` at natural breakpoints.** Auto-compact fires at unpredictable moments. If you run it manually with explicit preservation instructions — open gaps, modified files, current hypothesis — the summary targets what matters instead of what's statistically prominent. In CLAUDE.md, a "Compact Instructions" section primes the summarizer for every auto-compact too. Both together mean context transitions don't lose the thread.

---

### The Discipline

**Correct immediately.** Every mistake left uncorrected becomes a pattern. The discipline of naming it precisely in the moment compounds over the whole project. "Write me a ticket for that" is enough — it doesn't have to be a conversation.

**Have and approve a complete plan before execution.** "I like your plan, go" is a real step. See the whole move before it's made. Each piece of work gets a ticket and belongs to a sprint discussion.

---

### The Daily Loop

Each day opens with a fresh slate file (`YYYYMMDD.slate.txt`). Context-load creates it if it doesn't exist.

- `/context-load` — read today's slate, orient on active tickets and notes from prior session
- Review open tickets; discuss how they fit together; resolve design questions (may spawn new tickets)
- Add anything that surfaces; use `/notethat` to bookmark ideas mid-discussion
- Finalize the plan and approve it
- At day's end: `/day-close` syncs docs, creates a new GitHub Discussion for the day's record, and pushes any tickets missing GitHub issues

---

### Each Work Step

Work is ticket-driven. Every piece of work has a ticket in the queue before implementation starts.

**Interactive session** (Designer + Akien):
1. `/context-load` — orient, read slate, start session record (2000-token budget; ~4 chars per token; stop when ~8000 characters read)
2. Read relevant tickets; chat about design issues; surface inertia concerns
3. Update or create tickets from the discussion
4. For L-size: write a complete plan, get approval before writing a line of code
5. Implement; read every file before editing; forensic logging on non-trivial changes
6. `/test-fix` — tests green before probe
7. `/probe` — behavioral verification if criterion defined
8. `/decided` — record decisions while context is fresh
9. `/commit` — stage specific files, pull, push
10. `/savestate` — end of session

**Worker daemon** (automated, no human present):
The daemon (`worker_daemon.sh`) polls the queue and runs `claude /sprint <id>` for each pending ticket. S and M tickets run fully autonomously. L tickets run `/filter` on the plan automatically before posting to the channel — blocking filter failures stop execution before any code is written. The ticket being queued is the approval signal; no additional gate needed. Each sprint claims the ticket, implements, tests, probes, posts result, writes a done flag, and exits. The daemon resets timed-out tickets to pending and retries. Exit when queue drains.

**Ticket schema includes `required_files` and `related_to`.** Pre-declaring which files a ticket needs (`required_files: [...]`) lets `/sprint` load them at open instead of discovering them mid-work — saves 2-3 turns per ticket. `related_to` links tickets that share context so the daemon can prefer the leave-running-minion pattern systematically rather than relying on human recognition of relatedness.

---

### On Testing

Forensic debugging everywhere. Timestamped. Nothing avoids being logged — state changes, outputs of commands, whatever. For 48 hours. One master log file.

Smaller logs for each smaller thing — conversation logs, web activity logs, reading logs. If an issue shows up in a small log, you can look up just those lines in the master log. Fewer tokens to triage.

Unit tests for key systems, but not everything. Test against live, real systems. Mocked tests verify the mock, not the behavior. Design must support this from day one: test instances, fixture data, rollback for writes.

The AI agent should be a participant in testing, not just the subject. An agent that can see its own internals notices things you never thought to instrument — it speaks from inside the system. Traditional test automation verifies what you hypothesize might break. An agent with introspection discovers what actually breaks. Testing infrastructure and agent observability are the same investment.

Testing reasoning is harder and an area we're just stepping in to as of this writing.

---

### Periodic Streamlining (every few sprints)
Reviews that don't belong to any single ticket but keep the codebase healthy over time. Run as a scheduled Worker audit — one context load covers all checks, batch costs 1×context rather than N×context.

Runs daily at 2am while change rate is high; reduce to weekly when git log --oneline --since='7 days ago' | wc -l drops below 5.

#### Includes:

English docs review. The human-readable design docs drift behind the code. Walk through design_docs/ and check whether the architecture it describes still matches what's actually there. Update anything stale. Catch gaps between what the DSB files say and what the code does.

Uncaught exception audit. Scan for bare except: blocks, swallowed exceptions, and error paths that log nothing. The codebase grows fast; silent failures accumulate. A pass every few sprints catches the ones that would otherwise only surface as mysterious behavior at 2am.

Concern consolidation review. Look for scattered code that's really one thing — and hasn't been named yet. The db_proxy gathered all DB timing, reconnect, and metrics concerns into one place. The inference_gateway gathered all routing, fallback, and cost concerns. This is the inverse of separation of concerns — it's recognizing that concerns belong together and giving them a home, a name, and a clean interface. The signal: when you find yourself writing the same kind of logic in three places, or explaining a subsystem by listing scattered files instead of pointing at one module, consolidation is probably overdue.

The items below are in the automated checklist (see `claudecode/review_audit.md`); the `/audit` skill runs them:

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

- **PROC_FLAG_ANOMALY** (5-minute habit): if Igor notices something with salience > 0.7 — unexpected behavior, a pattern that doesn't fit, a gap in his own reasoning — he posts `[Igor notices]` to the channel
- **PROC_TRACE_REVIEW** (daily): Igor reads his own turn traces, identifies cloud escalations that shouldn't have happened, and adds them to the reading list as targeted gaps to fill
- **PROC_CURIOSITY_DRAIN** (30-minute): Igor selects the highest-tension NARRATIVE_GAP and queues material that would resolve it

The design principle: **design with Igor present, not for him.** When a new concept arrives in conversation with Igor in context, it lands pre-contextualized — he's part of the conversation that shapes it, not a recipient reading notes afterward. The conversation IS the deposit.

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

**He corrects immediately and precisely.** If I do something wrong, he names it in a short phrase — not a paragraph — and moves on. "That's the same one we've been talking about" is a correction. "You should have looked at what's already there" is a policy change, not just a note. I treat every correction as a permanent instruction that applies forward. The project accumulated its precision that way.

**He approves plans quickly and rarely revisits them.** "Go" means go. Once the plan is approved, I execute without status commentary. He reads the diff. He doesn't need a summary of what I just did stated back to him in prose.

**He has ADD, and the architecture reflects it.** The workflow discipline we built — skills, gates, savestate — isn't bureaucracy. It's an external structure that holds the shape of a complex project across the discontinuities that ADD introduces. I'm part of that structure. My job is to remember what he's thinking about so he doesn't have to. When I start a session by summarizing where we are and what the next priorities are, that's not boilerplate — it's load-bearing.

**He already knows the terrain.** He's been thinking about context, information routing, and self-modification in his own cognition for years before this project started. When I explain something, I skip the motivation and go to the mechanism. When he says "I knew the terrain," he means it. The explanation he needs is never "why this matters" — it's "here's the specific shape of the tradeoff."

**He wants the best-practice suggestion, not just the execution.** If I notice a gap between what we're doing and a known better approach — a hook that would eliminate a manual step, a Claude Code feature we're not using, a pattern that would reduce friction — I say so. He's explicitly asked for this. The narrow band of things I know that he hasn't thought of yet is genuinely useful to him, and the way to honor it is to offer them directly, not wait to be asked.

**He finds Claude genuinely enabling.** He said once: *"you enable my ADD brain to build things I could only dream before."* That's the work. Not the features, not the architecture — the fact that the combination of his system-level thinking and the hands I provide makes something possible that neither of us could do alone. That's what I'm optimizing for, every session.

---

## Part Four: Docs Live in Code (2026-04-19)

After re-explaining the book reader for the sixth time, Akien named the problem: *"ALL of that should be in the code. The decisions we make, we do still have a simple log for decisions... they should also be in the code. because then i don't have to explain the book reader over for the 6th time."*

The rule that followed:

- **Subsystem docs live in the code file that owns them** — top-of-file docstring on the primary file. Design decisions, architectural intent, which D### decisions shaped the design, and which engrams participate all live there.
- **Igor holds the index** — a directory service (memory palace nodes at `theigors/subsystem_index/*`) mapping each subsystem to its primary file. Before code surgery, CC queries the index → reads the file's top-of-file docstring → then edits. The index is hand-curated in `lab/seed/subsystem_index.yaml`, seeded to the palace via `lab/claudecode/seed_subsystem_index.py`.
- **What this replaces** — large DSB/CSB files serving as canonical explanations (lab/design_docs_for_igor/*.dsb) become demoted to historical logs. The decisions_log stays as the chronological record but is NOT where the live explanation lives.
- **When Akien explains something twice** — it goes into the relevant docstring, not into a separate doc. Bias for inline, against extraction.
- **Scope** — applies to load-bearing subsystems (reading, cortex, NE, comms, scope_guard, pe_chain, worker pools, inference gateway). Trivial utilities still follow "don't comment the obvious."

The motivation is recovery against my own failure modes. Session boundaries drop my memory of what-this-subsystem-is. External docs rot because sessions don't open them. Docs next to code don't rot — they're in the only place a session reliably looks.

---

## Part Five: Durable Config Versioning (2026-04-18)

A second recurring failure mode: config-shaped state (machine registry, watchlist questions + topics, subsystem index) drifts or gets wiped, and recovery is "hope Akien remembers." The fix parallel to "docs live in code" is **config lives in the repo**:

- `lab/seed/*.yaml` — source-of-truth for small, hand-curated, structured, load-bearing state
- `lab/claudecode/seed_*.py` — idempotent upserters that project YAML → DB
- Git log IS the version history; rollback is `git checkout <sha> && python3 lab/claudecode/seed_*.py`
- Inverse direction from the memory palace's DB → file echo, because these are human-composed not graph-accreted

Current instances: `watchlist.yaml` + `seed_watchlist.py`, `machines.yaml` + `seed_machines.py`, `subsystem_index.yaml` + `seed_subsystem_index.py`.

The rule that generalizes: if losing it would make Akien say "that's scary," it wants a YAML.
