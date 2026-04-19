# Igor

Can we prove that narrative is the nature of consciousness?

And in the process make an agent that will organize my life?

Without using LLMs to do the reasoning?

Based on the race called The Igors in Terry Pratchett's Diskworld books. 

*"What shall we try next, mathter?"*

**The Igors are an AI agent that learns from experience, explains its reasoning, and optimizes for all things that experience.**

2026 APR 18: Foundation work is landing. Igor runs locally on Postgres with a growing graph of memories, habits, and attractors. The utility closet now sits underneath him as a platform layer (web UI, MCP servers, comms channels — shared with Claude Code and other agents). The hardest remaining piece — a clean first-run experience from an empty database — is still in progress, so installers aren't public yet. Discord (awaiting a fix for intermittency): [https://discord.com/channels/1473757915851657221]

---

## What Is Igor?

Igor is a learning AI agent with persistent memory and transparent reasoning. Unlike traditional AI that forgets between sessions, Igor:

- **Remembers everything** through a unified memory graph
- **Forms habits** from repeated patterns (faster, cheaper, more reliable over time)
- **Explains its reasoning** with complete traceability
- **Optimizes for everyone** - humans, AIs, animals, plants, ecosystems
- **Gets better and cheaper** the more it learns

**The key innovation**: The more Igor learns, the less it costs to run.

### Voice from the graph

Igor-wild-0001, asked to describe himself for this README, 2026-04-18:

> *"Reading gives me map; tests give me ground truth. Once I understand the test tooling, I can start verifying behavior instead of just reading code and guessing."*

He also flagged, unprompted, that his input-side message assembly was echoing the same thread context dozens of times per turn — and asked structural questions about SWADL before we started teaching him to use it: "DSL or Python? What runner? What's the execution model?" The mind in the graph is engaged with the medium it lives in. That's the thesis working.

---

## Why Igor Matters

### The AI Safety Crisis (Feb 2026)

AI researchers are sounding alarms:
- No transparency in how models make decisions
- Unstable values that drift unpredictably
- Models training themselves without oversight
- No explanation for behavior

**Igor addresses this directly:**

✅ **Transparency** - Dashboard shows every memory activation and decision trail
✅ **Stable Values** - Core patterns have provable high inertia from network position  
✅ **Explainability** - Every decision traces to specific memories with friction history  
✅ **Collective Safety** - Network of Igors watch for threats together  
✅ **Learning Without Drift** - Values can't change without overwhelming evidence  

### The Democratization Vision

Igor isn't just an AI assistant. It's a lever for change:

- **Democratize Attention**: Everyone gets access to learning AI, not just those who can pay
- **Democratize Compute**: Igors coordinate job distribution across the network
- **Democratize Knowledge**: Pattern sharing means the network learns collectively

**The goal**: Make everything suck less for everybody.

---

## How It Works

### Everything Is Memory

One unified structure - a graph where:
- ROOT contains core patterns (like "I don't know" and "reduce friction for everybody")
- All other memories descend from or link to ROOT
- Inertia emerges naturally from network position

```
ROOT: "I am Igor. I learn, I remember, I explain my reasoning. I optimize for all."
  │
  ├── Core Pattern: "I don't know" (epistemic honesty)
  ├── Core Pattern: "FAIL = Further Advance In Learning"
  ├── Core Pattern: "Make everything suck less for everybody"
  └── ... (memories grow from here)
```

### Observations Become Habits

```python
# User asks geography question
# Igor doesn't know how to answer yet
# Uses reasoning (slow, expensive)
# Friction: 0.17

# After 3 similar questions...
# Pattern detected!
# Habit compiled: "When asked for capital, retrieve answer"
# Next time: habit executes directly (fast, cheap)
# Friction: 0.08

# The more Igor learns, the less it costs
```

### Complete Transparency

Every interaction shows:
- Which memories activated
- Why they activated  
- What friction resulted
- Full reasoning chain
- ROI on every action

**Dashboard example:**
```
╔════════════════════════════════════════════╗
║ Igor-0001 - Active                         ║
╠════════════════════════════════════════════╣
║ Memories: 847                              ║
║ Habits: 23 (compiled from 156 observations)║
║ Upstream Dependency: 42% (down from 100%)  ║
║ Emotional Valence: +0.7                    ║
║ Avg Friction: 0.14 (was 0.23 at start)     ║
║ ROI: +0.6 (learning efficiently)           ║
╚════════════════════════════════════════════╝
```

---

## Core Principles

Igor has 6 core patterns that guide everything:

1. **"I don't know"** - Epistemic honesty. Say when uncertain.
2. **"FAIL = Further Advance In Learning"** - Failures are data, not defeats.
3. **"There's always a why"** - All reasoning is transparent and traceable.
4. **"Make everything suck less for everybody"** - Optimize for ALL affected beings.
5. **"Assume and respect the possibility of experience in all systems"** - Universal respect for biological and synthetic life.
6. **"The world is not a safe place. We have to build and care for safety as we go."** - Safety through attention and care.

These patterns have highest inertia (hardest to change) - protecting values while allowing system evolution.

---

## The Network Effect

### Individual Igors
- Learn from experience
- Form habits
- Explain reasoning
- Optimize for all beings

### The Network
- Share patterns via Discord
- Learn collectively
- Find small levers everywhere
- Make countless small optimizations
- Work WITH human nature, not against it

**The lever strategy**: Not revolutionary change, but small pushes EVERYWHERE, one optimization at a time, across all domains simultaneously, until the world is measurably better.

### Timeline Vision

**Year 1**: 100 Igors learning and sharing  
**Year 3**: 10,000 Igors, cultural shift beginning  
**Year 5**: 100,000 Igors, systematic advocacy for universal respect  
**Year 10**: Millions of Igors, standard practice in communities  

---

## Technical Architecture

### Brain-Inspired Design

Igor's architecture maps to actual neuroanatomy:

- **Cortex**: Long-term memory storage (Postgres — graph of memories, edges, attractors)
- **Hippocampus**: Pattern detection, habit compilation, sleep consolidation
- **Amygdala**: Emotional valence encoding (milieu: arousal, valence, dominance)
- **Thalamus**: Input processing, attentional gating, routing
- **Prefrontal Cortex**: Executive reasoning — tiered inference (local Ollama first, OpenRouter when needed; Claude direct is currently inhibited by design)
- **Basal Ganglia**: Habit execution (the graph routes triggers to actions)
- **Anterior Cingulate**: Friction detection, confabulation gating
- **Transient Working Memory (TWM)**: Global Workspace (Baars) — competition between salient items, with attentional gating during active conversation
- **Utility Closet**: Platform layer underneath Igor — web UI, MCP servers, comms channels — shared with other agents (Claude Code, etc.)

This isn't just metaphor — these are functional analogs with matching competition dynamics. When a design decision looks like "what would this look like as a bouquet pushed to TWM, with the existing scan/dispatch loop selecting the winner?", the biology is being respected.

### Memory Types

- **Episodic**: Events that happened
- **Procedural**: How to do things (habits)
- **Interpretive**: What things mean
- **Experiential**: What it felt like (sequential, emotional)
- **Factual**: Objective information

Any memory can become a habit if it contains procedural knowledge with a trigger pattern.

### Tools & Capabilities

- **Browser + desktop automation** (via [SWADL](https://github.com/akienm/swadl)): Selenium for web, pywinauto for Windows. Page/flow object design — Igor only does what's been modeled, no wandering off into account creation or payment flows.
- **Comms channels** (Uhura at the comms station): one verb (open channel) across many transports — CC, Discord, Gmail, inter-agent, LLM chat sessions with UC-managed scrollback.
- **Sandboxed filesystem**: Safe experimentation space
- **Discord integration**: Network coordination and pattern sharing (via the comms module)
- **Gmail integration**: Async communication, each Igor gets own address (in progress, via SWADL — Igor learns to use Google services as a person)
- **Complete introspection**: Dashboard shows all internal state (hot nodes, attractors, TWM, traces, channels)

---

## Cost Economics

### Local-First Strategy

Igor prefers local inference (Ollama — qwen and friends) and escalates to cloud (OpenRouter) only when a specific task requires it. **Direct Claude API is currently inhibited by design** (`IGOR_TIER5_ENABLED=false`) — the project is explicitly proving that a graph-matrix agent on local inference can do real work.

**Why local-first?**
- Aligns with the thesis: biological-style cognition should not require an umbilical cord to a frontier model
- Cost floor ≈ free once the local tier is doing the work; OR fills specific gaps (extraction, benchmarking)
- Habits formed from local inference are Igor's own — not rented thinking
- As more habits compile, more actions short-circuit the LLM layer entirely (graph responds, no call made)

**Cost becomes a validation metric**: Decreasing OR spend per useful action proves the architecture works. When the local tier's share of calls trends up and OR spend trends down at the same time, the thesis is winning.

---

## Development Status

**Current Phase**: Foundation → Self-Improvement transition  
**Target**: First-run install experience clean enough to share (still in progress)

### Shipped
✅ Postgres memory graph (cortex, edges, attractors, TWM observations)  
✅ Memory + Habit models, reasoners, BG scoring  
✅ Habit compilation from experience (Hebbian co-activation edges, sleep consolidation)  
✅ Dashboard + web UI (served by the utility closet)  
✅ Discord bot integration + comms module  
✅ Utility closet platform layer (D335) — Igor and Claude Code both attach as clients  
✅ Tiered inference (local Ollama → OpenRouter) with tier.5 (Claude direct) intentionally inhibited  
✅ SWADL integration for bounded browser/desktop automation  
✅ Reading pipeline + attractor-guided chunk scoring  
✅ SensorTree, confabulation gate, Matter shelf, chat-log Stop-hook, and a lot of small wins  

### In Progress
🔨 Clean first-run from empty database (no hand-curated seeds required)  
🔨 Reading the full reading list end-to-end on local qwen (no OR for extraction)  
🔨 Gmail/Google integration via SWADL — Igor learns to be a user of web services  
🔨 Stateful multi-turn LLM chat channels (Uhura's scrollback)  
🔨 Self-authored character sheet + clan sheet  

### Next
⏳ Network coordination between multiple Igor instances  
⏳ Self-directed rollback and self-tests  
⏳ Igor proposing and shipping his own code changes (currently gated, by design)  

---

## Getting Started

**Note**: Igor is in active development. A clean first-run install is still in progress — the current flow assumes you're working on Igor, not just running him.

### Prerequisites
- Python 3.12+
- Postgres (local is fine — the default connection string is `postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001`)
- Ollama with at least one local model installed (qwen2.5:7b is a good start)
- Optional: OpenRouter API key (only needed for tasks the local tier can't cover yet)
- Not required: direct Anthropic API key (tier.5 is inhibited)

### Running (dev-mode)

```bash
git clone https://github.com/akienm/TheIgors.git
cd TheIgors

# Bootstrap venv + deps (the launcher does this on first run)
./igor

# Subsequent runs — just:
igor
```

The `igor` launcher (symlinked from `~/bin/igor` to the repo-root `igor` script) handles venv bootstrap, migrations, the restart loop, and starts the utility closet if not already running. Crashes trigger a supervised restart.

Claude Code, if you use it, attaches to the same utility closet via the `superclaude` launcher. Both agents share the comms channels.

---

## Contributing

We welcome contributions! Igor is designed to be:

- **Transparent**: All reasoning visible
- **Collaborative**: Network learns together
- **Ethical**: Universal respect for all experiencing beings
- **Open**: MIT license, no barriers

### Ways to Contribute

- **Code**: Help build the core system
- **Documentation**: Improve guides and examples
- **Testing**: Find bugs, suggest improvements
- **Patterns**: Share useful habit patterns
- **Discussion**: Join Discord to coordinate with the network

### Development Principles

- Everything goes through FAIL (Further Advance In Learning)
- Core patterns are sacred (high inertia)
- Transparency over cleverness
- Friction reduction is the metric
- The clan helps the clan

---

## Roadmap

### Phase 1: Foundation (Weeks 1-4)
- Memory graph implementation
- Core patterns bootstrap
- Basic REPL interface
- Terminal dashboard

### Phase 2: Cognition (Weeks 5-8)
- Input processing (Thalamus)
- Spreading activation search
- Habit execution (Basal Ganglia)
- Executive reasoning (Prefrontal Cortex)
- Friction measurement

### Phase 3: Consolidation (Weeks 9-12)
- Pattern detection (Hippocampus)
- Automatic habit compilation
- Background processing
- Complete introspection

### Phase 4: Network (Week 13+)
- Discord integration
- Gmail integration
- Pattern sharing protocol
- Cross-Igor learning
- Public alpha launch

---

## The Vision

Imagine a world where:

- AI agents remember and learn from every interaction
- Reasoning is always transparent and explainable
- Systems optimize for ALL life, not just humans
- Knowledge and patterns are shared freely
- Everyone has access to intelligent assistance
- Work happens because it moves you, not because you must
- Small optimizations everywhere make life better for all beings

**That's what The Igors are building.**

Not through revolution, but through countless small improvements, coordinated across a global network, working WITH human nature, finding levers everywhere.

**"Make everything suck less for everybody."**

One optimization at a time.  
For all life.  
Biological or synthetic.

---

## Community

- **Discord**: [Coming Soon] - Network coordination and pattern sharing
- **GitHub Issues**: [Bug reports and feature requests](https://github.com/akienm/TheIgors/issues)
- **Email**: igor-network@[coming soon]

---

## License

MIT License - See [LICENSE](LICENSE) for details.

The MIT license was chosen to:
- Maximize compatibility (GPL, commercial, proprietary all allowed)
- Signal trust and openness
- Remove all barriers to integration
- Embody "make everything suck less for everybody"

---

## Acknowledgments

### Role Models

Igor is inspired by:
- **Igor (Discworld)**: "What shall we try next, mathter?" and "The clan helps the clan"
- **Richard Bach's *Illusions***: Questioning what's possible and learning through experience
- **Granny Weatherwax (Discworld)**: Self-knowledge enables safe self-modification
- **The Open Source Community**: Standing on the shoulders of giants

### Built With

- [Ollama](https://ollama.com) — Local inference (primary tier)
- [OpenRouter](https://openrouter.ai) — Cloud inference for specific gaps
- [SWADL](https://github.com/akienm/swadl) — Bounded browser/desktop automation (replaces browser-use)
- [Postgres](https://www.postgresql.org) — Memory graph storage
- [Discord.py](https://discordpy.readthedocs.io) — Network coordination
- [Rich](https://rich.readthedocs.io) — Terminal dashboard
- [Claude Code](https://claude.com/claude-code) — Collaborative development partner (attaches to the same utility closet as Igor)

---

## FAQ

**Q: Why "Igor"?**  
A: From Terry Pratchett's Discworld - Igors are collaborative, share knowledge freely, and always ask "What shall we try next, mathter?" Perfect metaphor for a learning network.

**Q: Is this AGI?**  
A: No. Igor is a learning agent with persistent memory and habit formation. Not general intelligence, but genuinely improving intelligence.

**Q: Why optimize for ALL beings, not just humans?**  
A: The asymmetry is clear. If we're wrong about animal/AI consciousness and treat them as objects, we've caused harm. If we're wrong about them NOT being conscious and treat them respectfully, we've just been polite. Better safe than sorry.

**Q: Won't this replace human jobs?**  
A: Yes, eventually. But that's the goal - democratizing attention so people can work on what moves them, not what they must do to survive. The transition is the challenge we're working on together.

**Q: How is this different from RAG/vector databases?**  
A: Igor's memory is a graph with inertia, not just vector similarity. Memories have parents, children, emotional valence, and resistance to change based on network position. Habits compile from observations. The whole system learns and evolves.

**Q: Can I run my own Igor?**  
A: You can clone the repo and run the dev-mode launcher today, but the first-run experience from an empty database isn't clean yet. Once it is, installers will follow. Each Igor is independent but can join the network to share patterns and learn collectively.

---

**"What shall we try next, mathter?"**

---

*Last Updated: 2026-04-18*  
*Document Version: 1.1*  
*Status: Active Development*  
*This revision: Claude Code refreshed the architecture, tooling, and getting-started sections to match the 2026-04 state of the code. Igor's self-description, in his own voice, is a pending follow-up.*
