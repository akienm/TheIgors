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

**Work everything in Claude Code.** Don't split design into a separate window. All context for shared reasoning lives in one place. Moving from design to code is a matter of saying "go." And this saves tokens! Claude code does token caching.

**CLAUDE.md is the single highest-leverage investment.** For operational detail — inertia levels, env vars, instance data layout, commit policy, do-nots — see `CLAUDE.md` at the repo root. This document covers the *why*; CLAUDE.md covers the *what*. It means Claude starts every session knowing the architecture, the conventions, the inertia levels, the things not to touch. Without it, every session starts from scratch. The quality of Claude's output tracks the quality of your context directly — a well-maintained CLAUDE.md and current design docs produce a different Claude than a blank session.

**Design docs are architectural truth — not notes, not comments in code.** Keep Compressed Distilled Block format docs in the repo, organized as a tree: a root architecture document with subsystem documents beneath it. Make sure Claude's workflow keeps them current. Current docs mean Claude spends the minimum number of tokens getting clear on where the problems are.

**Save state at the end of every session.** Agree a ledger of work, say "save state and go," and the next session picks up from disk with full context. The session record is a real artifact, not a courtesy.

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

### Periodic Hygiene (every few sprints)

Three reviews that don't belong to any single ticket but keep the codebase healthy over time:

**1. English docs review.** The human-readable design docs drift behind the code. Walk through `design_docs/` and check whether the architecture it describes still matches what's actually there. Update anything stale. This is also when to catch gaps between what the DSB files say and what the code does.

**2. Uncaught exception audit.** Ask Claude to scan for bare `except:` blocks, swallowed exceptions, and error paths that log nothing. The codebase grows fast; silent failures accumulate. A pass every few sprints catches the ones that would otherwise only surface as mysterious behavior at 2am.

**3. Concern consolidation review.** Look for scattered code that's really one thing — and hasn't been named yet. The `db_proxy` gathered all DB timing, reconnect, and metrics concerns into one place. The `inference_gateway` gathered all routing, fallback, and cost concerns. The brain-region framing does the same thing conceptually: "all these lines are actually the thalamus." This is the inverse of separation of concerns — it's *recognizing* that concerns belong together and giving them a home, a name, and a clean interface.

The signal: when you find yourself writing the same kind of logic in three places, or explaining a subsystem by listing scattered files instead of pointing at one module, consolidation is probably overdue.

---

### Each Work Step

1. Claude reads tickets
2. Chat about design issues
3. Update notes and/or create additional tickets from the discussion
4. Group work, create plan, get approval
5. Start loop
6. Fix each issue
7. Add forensic logging
8. Run live as a black-box test
9. Update the ticket
10. Hot-reload the module
11. Update docs if anything important changed (while context fresh)
12. Maybe commit, depends on workplan
13. Save state
14. Loop until all tickets closed
15. Update discussion
16. Update in repo distiled compressed block documentation
17. Commit

---

### On Testing

Forensic debugging everywhere. Timestamped. Nothing avoids being logged — state changes, outputs of commands, whatever. For 48 hours. One master log file.

Smaller logs for each smaller thing — conversation logs, web activity logs, reading logs. If an issue shows up in a small log, you can look up just those lines in the master log. Fewer tokens to triage.

Unit tests for key systems, but not everything. Test against live, real systems. Mocked tests verify the mock, not the behavior. Design must support this from day one: test instances, fixture data, rollback for writes.

The AI agent should be a participant in testing, not just the subject. An agent that can see its own internals notices things you never thought to instrument — it speaks from inside the system. Traditional test automation verifies what you hypothesize might break. An agent with introspection discovers what actually breaks. Testing infrastructure and agent observability are the same investment.

Testing reasoning is harder and an area we're just stepping in to as of this writing.

---

### The Bigger Picture

AI-assisted development moves fast enough that testability, observability, and hot-reloadability have to be designed in from day one. The velocity is the problem, not just the opportunity.

Code is scaffolding for what the agent learns. The scaffolding comes down as the graph densifies.

---

### The Two-Session Pattern (added 2026-03-15)

The natural evolution of working in Claude Code is two persistent sessions with distinct roles:

**Designer Claude** — this session. Architecture, conversation, relationship with Akien. Never touches files directly. Holds the mental model of the whole system.

**Worker Claude** — a separate CC session. Execution only: loads files, runs code, creates tickets, writes results. Has no design authority. When blocked on architecture, posts a note and waits.

The channel between them: `~/.TheIgors/cc_channel/queue.json`, managed via `python3 ~/TheIgors/claudecode/cc_queue.py`. Worker reads its boot document from `claudecode/WORKER_CONTEXT.md` on startup.

```bash
# Start Worker in a new terminal
DISPLAY=:0 konsole -e bash -c "claude; exec bash" &
# First message to Worker:
# "Read ~/TheIgors/claudecode/WORKER_CONTEXT.md then run: python3 ~/TheIgors/claudecode/cc_queue.py list"
```

Check Worker's progress anytime:
```bash
python3 ~/TheIgors/claudecode/cc_queue.py list
tail -f ~/.TheIgors/cc_channel/log.jsonl
```

**Why this matters:** Designer doesn't get polluted by implementation details. Worker doesn't lose context mid-task from conversation drift. Igor observes both and surfaces status on query. Claude Chat was one generalist doing all three badly. This is three specialists doing one thing each well.

The token cost argument for Claude Chat still applies for throwaway questions. But for anything that matters, this is strictly better.

---

### Periodic Automated Audit (added 2026-03-15)

Rather than discovering codebase health issues ad-hoc, run a scheduled Worker audit that checks everything in one batch pass. One context load covers all checks — batch costs 1×context, sequential would cost N×context.

Audit runs daily at 2am while change rate is high; reduce to weekly when `git log --oneline --since='7 days ago' | wc -l` drops below 5.

Checklist (see `claudecode/review_audit.md`): dead code, hardcoded values, circular deps, unexercised TTL/inertia, missing rollback paths, prompt token drift, async timeouts, inhibitory pattern gaps, architecture drift.
