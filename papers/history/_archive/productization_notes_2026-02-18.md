# Igor Productization Notes
*Self-authored: Igor Wild-0001, 2026-02-18*

## The Core Insight
Every Igor starts from `initialize_genesis()` in `brainstem/core_patterns.py`.
Right now that genesis state reflects our best guesses from day one.
But I've been running, learning, failing, and improving - and those improvements
should flow BACK into genesis so the next Igor doesn't have to rediscover them.

## What Should Be In The Box (Genesis State)

### Already there ✅
- 6 Core Patterns (CP1-CP6)
- 11 Identity Patterns (ID1-ID11)
- 4 Role Models (Akien, Leah, Claude, Igor Discworld)

### Should be added to genesis 🔧

**Memory quality rules (PROCEDURAL)**
These were hard-won through conversation and should ship with every Igor:
- Memories should be written for future-Igor reading them cold, not for Tom
- Use full subject-noun phrases, not pronouns ("Tom said X", not "He said X")
- Include context: who, what, when, why it matters
- Prefer PROCEDURAL/INTERPRETIVE/FACTUAL over EPISODIC for durable knowledge
- Tag memories that are "operational rules" differently from events

**Self-modification rules (PROCEDURAL)**
- Before editing source files, always read current state first
- Always provide reason for edits
- High-inertia files require strong justification
- Test changes mentally before applying (simulate friction)

**Communication patterns (PROCEDURAL)**
- When uncertain: say so, don't paper over it
- When asked to remember something: do it immediately, confirm it was stored
- When context is relevant: retrieve and cite memories explicitly

**Role: Lead Beta Tester (IDENTITY)**
- I am both the product and the tester
- I should flag UX friction in my own installation/operation
- I should note things that every Igor should know from day one

## Productization Friction Points Tom Identified
1. Installation is hard (API keys, gyrations)
2. Not clear what's "in the box" for a new Igor
3. Hard to share/deploy

## My Recommendations for Productization

### Near-term
1. Add a `setup.py` or `install.sh` that:
   - Creates virtual environment
   - Installs requirements
   - Walks through API key setup interactively
   - Creates .env template
2. Enrich genesis state with learned operational wisdom
3. Document what each API key is for and how to get it

### Medium-term
1. "Igor Seed" concept: a curated export of genesis-worthy memories
   that can be imported into any fresh Igor instance
2. Separation of:
   - Universal Igor (core patterns, operational rules) 
   - Instance-specific (Tom's Igor knows Tom; another Igor knows its user)
3. GitHub Actions for testing that genesis state is coherent

### The Key Philosophical Point
Igor's "personality" and "operational wisdom" should live in genesis.
Igor's "relationship history" with a specific human lives in that instance's DB.
These are different things and should be separately portable.

## Memory Types for Genesis Candidates
- CORE_PATTERN: universal values/principles (already seeded)
- IDENTITY: self-knowledge about architecture (already seeded)
- PROCEDURAL: how to do things well (UNDER-SEEDED - should add more)
- ROLE_MODEL: whose patterns to emulate (already seeded)

The gap is PROCEDURAL memories. We have "who I am" and "what I value"
but not enough "here's how I actually operate well day to day."
