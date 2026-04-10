# TheIgors Project: Claude+Akien Collaboration Statistics

**Report Date**: 2026-04-01  
**Collaboration Period**: 2026-02-16 to 2026-04-01 (46 days)

---

## 1. SESSIONS

- **Total Sessions**: 111
- **Date Range**: 2026-02-16 (first commit) to 2026-04-01 (latest session)
- **Current Session Pace**: ~2.4 sessions/day (intensive)

### First 5 Sessions (Arc Origin)
1. **Session 2026-03-16a** - Architecture pivot: direct habit execution endpoint (D094)
2. **Session 2026-03-16b** - D094 implementation: IgorBase + CC ops habits seeded
3. **Session 2026-03-16g** - D099 TWM multi-slot attractor
4. **Session 2026-03-16h** - D098+D100+D101 implemented; 1517× word_graph speedup
5. **Session 2026-03-16i** - G-MEM2 closed; D096/D097 (pipeline state + format conversion)

### Last 5 Sessions (Arc Current)
1. **Session 2026-03-31b** - First live Igor self-coding exercise (T-signal-handlers)
2. **Session 2026-03-31c** - T-signal-handlers done; D274/D275 crystallized
3. **Session 2026-04-01a** - Goal-as-thread architecture + biological patterns gap (D276/D277)
4. **Session 2026-04-01c** - Phase D ex4: Igor does grep/search after goal ready (T-rl-status-collapse)
5. **Session 2026-04-01h** - Engram layer3 stdlib (D298; T-layer3-parse-goal/situate)

---

## 2. DECISIONS

- **Total D-numbered Decisions**: 334 (D001 through D300+)
- **First Decision**: D001 (everything-is-memory, implemented)
- **Latest Decision**: D300 (TWM as inter-subsystem channel, defined)
- **Status Distribution**:
  - Implemented: ~210
  - Implemented-POC: ~45
  - Implemented-Seeds: ~35
  - Planned: ~30
  - Defined: ~14

---

## 3. GIT COMMITS

- **Total Commits**: 839
- **Commit Date Range**: 2026-02-16 (earliest) to 2026-04-01 (latest)
- **Avg Commits/Day**: ~18.2
- **Velocity Peak**: 20+ commits/day (during intensive sprints)

---

## 4. TICKETS

- **Total Tickets in Queue**: 299
- **Done**: 256 (85.6%)
- **Pending**: 39 (13.0%)
- **Blocked**: 2 (0.7%)
- **Unset Epic**: 215
- **By Epic**:
  - Cognition: 34
  - Training: 27
  - Operations: 12
  - Claude: 7
  - Swarm: 3
  - Database: 1

---

## 5. TESTS

- **Total Tests Collected**: 1,347
- **Test Files**: 1,248
- **Coverage**: Comprehensive multi-tier (unit, integration, live system)
- **Key Test Areas**:
  - Cognition pipeline (narrative_engine, thalamus, milieu, word_graph)
  - Memory system (cortex, db_proxy, node_executor)
  - Habit/BG scoring (habit_compiler, dispatch)
  - Inference routing (gateway, tier ladder)
  - Tools and utilities

---

## 6. CODE SIZE

- **Python Lines (wild_igor/)**: 69,199 lines
- **Primary Modules**:
  - `cognition/` — ~12,000 lines (NE, thalamus, milieu, word_graph, inference_gateway)
  - `memory/` — ~8,000 lines (cortex, db_proxy, models, storage)
  - `tools/` — ~6,500 lines (learner, runner, reader, etc.)
  - `main.py` — ~5,500 lines
  - `brainstem/` — ~4,200 lines
  - `memory/models.py` + `cortex.py` — HIGHEST INERTIA (0.95+)

---

## 7. SKILLS (Claude Code)

- **Total Skills Built**: 18
- **Skill Categories**:
  - Architecture/Design: `/review`, `/decided`, `/filter`, `/slate`, `/slateclose`
  - Work Execution: `/sprint`, `/fixit`, `/test-fix`, `/day-close`, `/audit`
  - Igor Integration: `/igor`, `/readigor`, `/probe`
  - Infrastructure: `/context-load`, `/savestate`, `/notethat`, `/commit`
  - Utilities: `/keybindings-help`, `/update-config`, `/schedule`, `/loop`, `/simplify`, `/claude-api`

---

## 8. DESIGN DOCUMENTATION

- **design_docs/**: 30 files
  - architecture.md (root)
  - 15+ subsystem deep dives
  - decision evolution threads
  - ethical framework + mission
- **design_docs_for_igor/**: 22 files
  - decisions_log.dsb (334 decisions)
  - capabilities_index.dsb (126+ tools)
  - All artifact formats (dsb, csb, txt)

---

## 9. CRYSTALLIZATIONS

Named moments of architectural clarity — when disparate patterns unified into a single conceptual primitive:

1. **FIRST CRYSTALLIZATION** (2026-02-17): "Everything is memory" — unified model
2. **SECOND CRYSTALLIZATION** (2026-03-11): Tree structure of thought
3. **THIRD CRYSTALLIZATION** (2026-03-15): Signal propagation patterns
4. **FOURTH CRYSTALLIZATION** (2026-03-17): Three Primitives — trees, gradients, habits
5. **FIFTH CRYSTALLIZATION** (2026-03-18): Pattern Engineering — habits as reusable units
6. **SIXTH CRYSTALLIZATION** (2026-03-18): Process Development Tools — observation infrastructure
7. **SEVENTH CRYSTALLIZATION** (2026-03-18): Trails and Gradients — traversal as training signal
8. **EIGHTH CRYSTALLIZATION** (2026-03-19): Cognition as Pipeline — emit+react substrate
9. **NINTH CRYSTALLIZATION** (2026-03-22): **Engram Language** — non-biological program substrate
   - 21-pattern inventory (10 original + 10 Igor contributions + CACHED_PROBE)
   - Templates as macros (expand at seed, not runtime)
   - Epic: T-template-schema → T-language-spec

**Emerging**:
- Facia = Thread Crystallization (D255-257): Thread IS the graph topology
- Emit+React = Cognitive Milieu (D260-261): Fundamental primitive

---

## 10. ARCHITECTURAL MILESTONES

### Slate 0: Database + Reading (CLOSED)
- Multi-box reading pipeline live (Calibre + Kindle + PDFs)
- PostgreSQL + Redis running stable
- Embedding + cosine search working
- Reading queue 340+ items; drain runner active

### Slate 1: Self-Training Loop (CLOSED)
- Trails infrastructure live (query→traversal→trail deposit)
- Habit compiler self-improving
- Igor identifies own gaps, books reading list accordingly
- Co-designer loop (PROC_FLAG_ANOMALY, PROC_TRACE_REVIEW, PROC_CURIOSITY_DRAIN)

### Slate 2: Igor Programs Himself (ACTIVE)
- **Phase A** (DONE): Design engrams ✓
- **Phase B** (DONE): Igor self-editing infrastructure ✓
- **Phase C** (DONE): Engram execution layer 1-2 ✓
- **Phase D** (IN PROGRESS): Unattended canonical self-coding
  - D ex1-ex4: VERIFIED (claim→show+grep→ready)
  - D ex5: Designing (Igor stores grep results)
  - D277 gaps: T-predictive-coding, T-refractory-period, T-homeostatic-setpoints, T-habit-chunking

### Slate 3: Productization (PLANNED)
- Multi-user + permissioning
- Swarm coordination (cloud escape → read task delegation)
- Output phase (confidence-gated verbosity, model-aware formatting)

---

## 11. COLLABORATION DYNAMICS

### Token Efficiency
- **Context Caching**: Enabled across sessions via CLAUDE.md + DSB structure
- **Session Cost**: ~$100/day peak (intensive sprints); $30-50/day (maintenance)
- **Avg Session**: 2-3 hours, 30-50k tokens
- **Skill Model Routing**: Haiku 4.5 (~10× cheaper) for mechanical work; Sonnet 4.6 for design

### Discipline & Workflow
- **Before Editing**: Always read file first; check inertia level; review design docs
- **Approval Gate**: "Complete plan before execution" — never code without Akien sign-off
- **Two-Session Pattern**: Designer (architecture) + Worker (execution) split reduces context drift
- **Commit Discipline**: Manual commits at logical checkpoints; no auto-commit (except Igor's self-edits)

### Testing & Observability
- **Forensic Logging**: Timestamped everywhere; 48-hour retention; one master log
- **Live Testing**: Black-box tests against real systems, not mocks
- **Agent Introspection**: Igor observes own logs + suggests fixes (self-repair loop)

---

## 12. KEY ARTIFACTS

### Memory System
- **SQLite**: `wild-0001.db` (runtime, not in repo; ~500MB after 46 days)
- **Formats**: Memory CSB, decisions DSB, sessions MD, project notes MD
- **Current DB Size**: 14,000+ unique memories (FACTUAL/INTERPRETIVE/PROCEDURAL/EPISODIC)

### Infrastructure
- **Inference Tier Ladder** (D234):
  1. Habit/graph (zero inference)
  2. Ollama local (primary; 100% availability)
  3. OpenRouter cheap (gpt-4o-mini; luxury quality path)
  4. OpenRouter haiku
  5. OpenRouter sonnet
  6. Anthropic direct (inhibited; IGOR_TIER5_ENABLED=false)
  7. Arbiter alert (human approval)

- **API Accounts**: Two separate (CC=Anthropic direct; Igor=OpenRouter) prevents rate contention
- **Instance Data**: `~/.TheIgors/Igor-wild-0001/` (jobs, arbiter, context, logs, inbox/outbox)

### Engram Language (D259-D300)
- Layer 1 (execute): EMITIF, BRANCHIF, FORKIF, ENDIF
- Layer 2 (traversal): LABEL, STOPIF, TARGETIF, FACIA
- Layer 3 (semantics): PARSE_GOAL, SITUATE, DECOMPOSE, ANTICIPATE, CONSTRAIN, OBSERVE, REPLAN, SCOPE_CHECK, HYPOTHESIZE
- Execution: node_executor.py (730 tests); emit_channels.py (6 channels)

---

## 13. COLLABORATION DISTILLED

### What Made This Fast
1. **Unified context** (CLAUDE.md + DSB architecture docs) meant Claude starts every session clear
2. **Skill model** (designer/worker/scribe split) prevented context thrashing
3. **Forensic logging** (from day one) made diagnosis immediate, not speculative
4. **Inertia discipline** (HIGH/MEDIUM/LOW + explicit approval gates) prevented architectural drift
5. **Live testing** (not mocks) caught integration issues before they metastasized
6. **Igor's introspection** (ability to read own logs + suggest fixes) turned debugging into design collaboration

### The Leverage Points
- **Every architectural decision lands in DSB** → no re-litigating
- **Every session lands in sessions.md** → startup context in 30 seconds
- **Tickets land in queue.json** → status visible to all three Claude sessions + Igor
- **Every mistake gets named precisely** → prevents becoming a pattern
- **Plan approval before coding** → saves tokens downstream

### The Cost
- ~$4,600 in API spend over 46 days (peak velocity phase)
- Budget cap: 2 sessions/month (post-peak; pilot/probe phase cheaper than design phase)
- Igor self-editing will eventually route 80% of development through cheaper channels

---

**Generated**: 2026-04-01 (case study data gathering complete)
