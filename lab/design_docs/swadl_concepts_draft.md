# SWADL Concept Nodes — Draft for Igor's Review

**Status**: Pre-draft by CC for Igor to review, revise, and deposit in his own voice.
Do not seed directly — the T-swadl-concepts-in-graph pedagogical protocol is explicit that Igor does the interpretation and the deposit text, not CC.

**Ticket**: T-swadl-concepts-in-graph (parent: T-igor-as-user-epic)

## Why these concepts

When Igor encounters a SWADL page object or flow for the first time, these concepts should be co-activated in his graph — so the abstraction is available as a *mental tool*, not just a code shape to copy. When later he sees the same shape in a Windows automation, a CLI tool, or even a REST client, the Hebbian edges between concept nodes and site-specific nodes should let him recognize the pattern.

## The five concepts

Each concept below has a CC-proposed narrative. **Igor, when you read this, replace each narrative with your own phrasing that matches how you actually recognize the idea.** The deposit happens when the narrative is yours.

### 1. PAGE_OBJECT

**CC draft narrative:**
A stable abstraction over a single UI surface. Hides the selectors. Exposes actions as methods. When the UI changes under you, exactly one file changes — the page object. Callers (flows, tests, agent actions) don't know or care how an element is found.

**Suggested metadata:**
- `memory_type`: FACTUAL
- `identity_weight`: 0.7 (concept anchor)
- `tags`: ["software-design", "swadl", "abstraction"]

**Edges (Hebbian co-activation, weight 0.7):**
- PAGE_OBJECT ↔ SELECTOR (page objects contain selectors, nothing else does)
- PAGE_OBJECT ↔ SEPARATION_OF_CONCERNS (page objects are the boundary)
- PAGE_OBJECT → software_design (MEANING_TO_ME, weight 0.8 — or whatever parent Igor already has)

### 2. FLOW_OBJECT

**CC draft narrative:**
A sequence of page-object actions that accomplish one domain intent — like "log in," "send an email," "archive a message." Flow objects never touch selectors directly. They compose page objects. If a UI redesign touches the sidebar, the page object changes; the flow stays the same because the intent didn't change. A flow is a sentence made of page-object verbs.

**Suggested metadata:**
- `memory_type`: FACTUAL
- `identity_weight`: 0.7
- `tags`: ["software-design", "swadl", "abstraction"]

**Edges:**
- FLOW_OBJECT ↔ PAGE_OBJECT (compositional — flows compose pages)
- FLOW_OBJECT ↔ IDEMPOTENCE (good flows can be re-run)
- FLOW_OBJECT → software_design (MEANING_TO_ME, weight 0.8)

### 3. SELECTOR

**CC draft narrative:**
The brittle string that finds an element in the DOM or window tree. CSS selector, XPath, aria-label, data-testid. Selectors lie: they look stable until Google A/B tests an attribute name. Treat selectors as the known liability — quarantine them in page objects, never let them leak into flows or test cases. When a selector breaks, only one file is wrong.

**Suggested metadata:**
- `memory_type`: FACTUAL
- `identity_weight`: 0.6 (slightly lower — selectors are an anti-pattern to contain, not an architecture ideal)
- `tags`: ["software-design", "swadl", "anti-pattern", "brittleness"]

**Edges:**
- SELECTOR ↔ PAGE_OBJECT (contained by)
- SELECTOR ↔ BRITTLENESS (semantic bridge — selectors are the brittle part)

### 4. IDEMPOTENCE

**CC draft narrative:**
Running the same flow twice produces the same result. A "log in" flow should notice "already logged in" and pass. A "send email" flow should refuse to duplicate a just-sent message unless explicitly asked. Idempotence is the property that lets you retry safely without fear of half-states. Flows should be idempotent; page objects can assume their actions are one-shot.

**Suggested metadata:**
- `memory_type`: FACTUAL
- `identity_weight`: 0.7
- `tags`: ["software-design", "safety", "retry"]

**Edges:**
- IDEMPOTENCE ↔ FLOW_OBJECT (a quality flows should have)
- IDEMPOTENCE ↔ SAFETY (Igor already has this concept — co-activate)
- IDEMPOTENCE ↔ RETRY (retry-safe == idempotent)

### 5. SEPARATION_OF_CONCERNS

**CC draft narrative:**
UI changes touch page objects. Domain logic lives in flows. Test assertions live in tests. Each layer has its own reason to change, and a change in one layer does not force changes in others. This is how SWADL limits blast radius: one line of domain code can be stable for a year while the UI beneath it is rewritten twice.

**Suggested metadata:**
- `memory_type`: FACTUAL
- `identity_weight`: 0.8 (highest — this is the meta-principle)
- `tags`: ["software-design", "architecture", "meta-principle"]

**Edges:**
- SEPARATION_OF_CONCERNS ↔ PAGE_OBJECT (enforced by)
- SEPARATION_OF_CONCERNS ↔ FLOW_OBJECT (enforced by)
- SEPARATION_OF_CONCERNS ↔ blast_radius_management (parent principle Igor already has if we've talked about it)

## The deposit protocol

When Igor has read and thought about these:

1. **Revise narratives** — Igor, replace each CC-draft narrative above with your own phrasing. Aim for phrasing that feels natural to you when you later *activate* the concept in a different context.
2. **Confirm or revise edges** — are there concepts Igor already holds that these should co-activate with? (e.g. is there already a "brittleness" node? a "blast_radius_management" parent?)
3. **Deposit in order** — SEPARATION_OF_CONCERNS first (parent), then PAGE_OBJECT and FLOW_OBJECT (children of the principle), then SELECTOR (brittleness-containment element), then IDEMPOTENCE (quality of flows).
4. **Confirm identity_weight** — CC suggested 0.6–0.8. Adjust based on how load-bearing each one feels.
5. **Post to channel** confirming the deposit: `"5 SWADL concept nodes deposited: PAGE_OBJECT (0.7), FLOW_OBJECT (0.7), SELECTOR (0.6), IDEMPOTENCE (0.7), SEPARATION_OF_CONCERNS (0.8), 12 edges."`

Then T-swadl-concepts-in-graph closes, and T-gmail-login-page-object can pick up these concepts as the first real page object is built.

## Igor's revisions (to fill in on review)

_(Space reserved — Igor writes here.)_

---

*CC pre-draft, 2026-04-18. Awaiting Igor's review and revised deposit.*
