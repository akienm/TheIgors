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

**Skills are compiled procedures, not prompts.** Claude Code skills (`.claude/skills/`) load only a name token at startup and expand to full instructions on invocation. Use them for any multi-step workflow you want to be repeatable and non-negotiable: `savestate`, `workstep`, `igor`. Each one is a contract. The skill runs the same way every time without having to re-explain the steps. If a workflow requires more than three turns to explain, write a skill.

**Hooks are better than instructions.** Claude Code hooks (`~/.claude/settings.json`) run on every matching tool call regardless of context length, memory state, or whether Claude "remembers" the instruction. A PostToolUse hook that runs `black` on every edited `.py` file never needs to be asked. A PreToolUse guard that blocks `rm -rf /` never gets overridden by a long session. If a policy needs to be enforced reliably, put it in a hook. Instructions can be forgotten; hooks cannot.

**Design docs are architectural truth — not notes, not comments in code.** Keep DSB format docs in the repo, organized as a tree: a root architecture document with subsystem documents beneath it. Make sure Claude's workflow keeps them current. Current docs mean Claude spends the minimum number of tokens getting clear on where the problems are.

**Save state at the end of every session.** Agree a ledger of work, say "save state and go," and the next session picks up from disk with full context. The session record is a real artifact, not a courtesy.

**Use `/compact preserve: [...]` at natural breakpoints.** Auto-compact fires at unpredictable moments. If you run it manually with explicit preservation instructions — open gaps, modified files, current hypothesis — the summary targets what matters instead of what's statistically prominent. In CLAUDE.md, a "Compact Instructions" section primes the summarizer for every auto-compact too. Both together mean context transitions don't lose the thread.

---

### The Discipline

**Correct immediately.** Every mistake left uncorrected becomes a pattern. The discipline of naming it precisely in the moment compounds over the whole project. "Write me a ticket for that" is enough — it doesn't have to be a conversation.

**Have and approve a complete plan before execution.** "I like your plan, go" is a real step. See the whole move before it's made. Each piece of work gets a ticket and belongs to a sprint discussion.

---

### The Daily Loop

- Review open tickets against the next milestone
- Discuss how they fit together; resolve open design questions (this may spawn new tickets)
- Add anything else that surfaces
- Finalize the plan and approve it

---

### Each Work Step

1. Claude reads tickets
2. Chat about design issues
3. Update notes and/or create additional tickets from the discussion
4. Group work, create plan, get approval
5. Save state
6. Notify user to run /compact, tell them to reply when done
7. Start loop
8. Fix each issue
9. Add forensic logging
10. Run live as a black-box test
11. Update the ticket
12. Hot-reload the module
13. Update docs if anything important changed (while context fresh)
14. Maybe commit, depends on workplan
15. Loop until all tickets closed
16. Update discussion
17. Update in repo distiled compressed block documentation
18. Commit

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

The items below are in the Automated checklist (see claudecode/review_audit.md):

Architectural - Scattered resource managers (DB, HTTP, config, loggers instantiated ad hoc), Parallel conditional trees (same if/elif logic duplicated across multiple locations), Implicit god objects (classes that grew beyond a single clear responsibility), Missing abstraction layers (raw SQL/HTTP in business logic, no service/repository layer), Hardcoded values (magic numbers, model names, ports, thresholds in logic)

Error Handling - Bare except or except Exception: pass (swallowed errors), Unlogged exceptions (caught but only printed, not sent to logging system), Silent None returns after catch (caller has no idea something failed), Missing timeouts and fallback paths on network/API calls

Dead & Zombie Code - Unused imports (especially post-refactor), Unreachable branches (conditions that can never be true), Commented-out code blocks (Claude's "safety net" habit), Functions defined but never called (old versions left behind), Stale TODO/FIXME comments (promises Claude made to himself)

Dependency & Coupling - Circular imports, Tight coupling via direct instantiation inside constructors, Hidden globals (functions silently reading module-level state)

Igor Cognitive Code Smells - Hardcoded weights/thresholds in cognition logic (salience, TTL, urgency — should be in DB or config), Bypassed TWM (direct writes to long-term memory skipping the, working memory layer), Emotional milieu mutation outside the diffusion function, Thread-local state leaking into shared state, Behavioral responses hardcoded instead of being weighted graph traversals (violates "code is the player, data is the character"), Boot sequence assumptions (code that assumes cold-start rather than being warm-context safe), Missing provenance metadata on new habit nodes

Performance & Token Efficiency - Redundant LLM calls (same question asked without checking TWM first), Missing memoization on deterministic lookups, Oversized context assembly (full blob built when only a slice is needed)

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
