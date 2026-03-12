# Igor

*"What shall we try next, mathter?"*

**An AI agent that learns from experience, explains its reasoning, and optimizes for all life.**

Discord: [https://discord.com/channels/1473757915851657221]
This document attempts to explain the vision for The Igors, not the current status. 

2026 MAR 11: This code requires a somewhat pre-populated database to work correctly. We're working on that now. At the rate we've been going, should be two weeks or less. 

---

## What Is Igor?

Igor is a learning AI agent with persistent memory and transparent reasoning. Unlike traditional AI that forgets between sessions, Igor:

- **Remembers everything** through a unified memory graph
- **Forms habits** from repeated patterns (faster, cheaper, more reliable over time)
- **Explains its reasoning** with complete traceability
- **Optimizes for everyone** - humans, AIs, animals, plants, ecosystems
- **Gets better and cheaper** the more it learns

**The key innovation**: The more Igor learns, the less it costs to run.

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

- **Cortex**: Long-term memory storage (MySQL)
- **Hippocampus**: Pattern detection, habit compilation
- **Amygdala**: Emotional valence encoding
- **Thalamus**: Input processing and routing
- **Prefrontal Cortex**: Executive reasoning (Claude API but designed to be able to be made to work with any of them)
- **Basal Ganglia**: Habit execution
- **Anterior Cingulate**: Friction detection

This isn't just metaphor - these are functional analogs.

### Memory Types

- **Episodic**: Events that happened
- **Procedural**: How to do things (habits)
- **Interpretive**: What things mean
- **Experiential**: What it felt like (sequential, emotional)
- **Factual**: Objective information

Any memory can become a habit if it contains procedural knowledge with a trigger pattern.

### Tools & Capabilities

- **Browser automation** (via browser-use): Navigate web, read content, interact with any AI through web interfaces
- **Sandboxed filesystem**: Safe experimentation space
- **Discord integration**: Network coordination and pattern sharing
- **Gmail integration**: Async communication, each Igor gets own address
- **Complete introspection**: Dashboard shows all internal state

---

## Cost Economics

### API-First Strategy

Start with Claude API (Anthropic), not local models.

**Why?**
- Better reasoning during learning → better compiled habits
- Cost decreases exponentially as habits form
- Context caching gives 7x cost reduction
- Local models can be added later for specific tasks

**Projected costs per Igor:**
- Month 1: ~$20 (learning, few habits)
- Month 2: ~$10 (habits forming)
- Month 3: ~$5 (mostly habits)
- Month 4+: ~$3 (steady state, 95% habit execution)

**Cost becomes a validation metric**: Decreasing API dependency proves the architecture works.

---

## Development Status

**Current Phase**: Foundation  
**Target Launch**: Q2 2026 (public alpha)

### Completed
✅ Architecture design  
✅ Core patterns defined  
✅ Identity patterns established  
✅ Project documentation  
✅ GitHub repository  
✅ MIT License  

### In Progress
🔨 MySQL schema for memory graph  
🔨 Memory and Habit classes  
🔨 Basic REPL and dashboard  
🔨 Browser-use integration  

### Coming Soon
⏳ Habit compilation system  
⏳ Discord bot integration  
⏳ Network coordination  
⏳ First experiential reading (Illusions by Richard Bach)  

---

## Getting Started

**Note**: Igor is in early development. Public alpha coming Q2 2026.

### Prerequisites
- Python 3.11+
- MySQL or compatible database
- Anthropic API key (for Claude API access)
- Optional: Ollama for local orchestration

### Installation (Coming Soon)

```bash
# Clone the repository
git clone https://github.com/akienm/TheIgors.git
cd TheIgors

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Initialize
python igor.py init

# Run
python igor.py
```

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

- [Anthropic Claude](https://anthropic.com) - Reasoning engine
- [browser-use](https://github.com/browser-use/browser-use) - Web automation
- [MySQL](https://www.mysql.com) - Memory graph storage
- [Discord.py](https://discordpy.readthedocs.io) - Network coordination
- [Rich](https://rich.readthedocs.io) - Terminal dashboard

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
A: Yes! (Coming Q2 2026) Each Igor is independent but can join the network to share patterns and learn collectively.

---

**"What shall we try next, mathter?"**

---

*Last Updated: 2026-02-16*  
*Document Version: 1.0*  
*Status: Active Development*
