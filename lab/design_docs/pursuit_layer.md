# Pursuit Layer — goal-bound behavioral units above engrams

*Decision D-pursuit-layer-2026-04-22. Initial draft 2026-04-22.*

---

## 1. The gap

Igor currently has two substrate levels and one invisible, implicit level:

| Level | Status | What it is |
|---|---|---|
| **Cells** | real (`memory/models.py`) | Graph nodes and edges — individual records, triggers, conditions, actions. |
| **Engrams** | real (`engram_language.md`) | Habits and templates: composed cell patterns that encode behavior. |
| **Goals** | **implicit / missing** | Whatever currently holds "what I was doing" across multiple engram firings. |

The third level exists in effect — things get done, sometimes — but it has no
primitives. There is no object named "what I'm currently trying to accomplish,"
no anchor for "I committed to this," no place to hang a completion test. When
an engram chain gets interrupted mid-flight, the in-flight state goes nowhere,
because there was nowhere for it to live.

**Pursuit** names that missing level and gives it primitives.

---

## 2. Biology grounding

The gap is familiar from biology. Three lines of work are load-bearing here:

### Schultz: phasic dopamine at commitment
Wolfram Schultz's electrophysiology (Schultz, Dayan, Montague 1997, and the
subsequent decade) showed that phasic dopamine is not a reward signal — it is
a **prediction error** signal that fires at three moments in a goal-directed
sequence: (1) when a goal-predictive cue appears and commitment forms
("anticipatory burst"), (2) at sub-goal achievements that update the
prediction, and (3) at final outcome if it diverges from prediction. The
anticipatory burst is the key one for us: dopamine rises at the *moment of
commitment*, not at the end. A system with no commitment object has no place
for that burst to attach.

### Graybiel: striatal chunking
Ann Graybiel's work on the basal ganglia (Graybiel 1998, "The basal ganglia
and chunking of action repertoires") shows that extended action sequences get
packaged into single executable units in the striatum — a "chunk" that fires
at start and end but is opaque in the middle. Pursuits are the chunk-object:
named-at-start, completion-tested-at-end, with the interior left to engram
firings.

### Miller-Galanter-Pribram: TOTE
*Plans and the Structure of Behavior* (1960) proposed the TOTE unit —
Test-Operate-Test-Exit — as the recursive primitive of goal-directed behavior.
Sixty-five years later this is still the closest architectural match to what
a Pursuit is: a thing that checks whether it's done, acts if not, re-checks,
and exits when done. Pursuits are TOTE units that carry dopamine.

### Dickinson-Balleine: goal-directed vs habitual
Action-outcome learning (goal-directed) and stimulus-response learning
(habitual) are dissociable systems (Dickinson 1985; Balleine-Dickinson 1998).
Devaluing the outcome degrades goal-directed behavior but leaves habits
intact. Engrams in Igor today are pure stimulus-response — a trigger fires
an action. Pursuits are the action-outcome complement: the representation
of *what the action was for*, so the system knows what to do if the
desired outcome stops obtaining.

---

## 3. The three-layer model

```
┌───────────────────────────────────────────────────────────────┐
│  Pursuits — goal-bound units, carry commitment and outcome    │
│  primitives: entry stimulus, goal-facia, dopamine trace,      │
│  completion test, recursive sub-Pursuits                      │
├───────────────────────────────────────────────────────────────┤
│  Engrams — behavioral patterns, stimulus→action               │
│  primitives: triggers, conditions, actions, templates         │
├───────────────────────────────────────────────────────────────┤
│  Cells — graph substrate, the raw memory material             │
│  primitives: Memory nodes, edges, metadata                    │
└───────────────────────────────────────────────────────────────┘
```

Each layer composes from the one below:
- Engrams are patterns of cell activation.
- Pursuits are goal-bound compositions of engram firings.

Each layer adds one capability the layer below cannot represent:
- Cells: *what exists*.
- Engrams: *what fires in response to what*.
- Pursuits: *what we are trying to accomplish and why*.

---

## 4. Pursuit primitives

```
PURSUIT {
  id:                string                  // unique per-instance
  name:              string                  // human-readable ("address_boredom")
  entry_stimulus:    StimulusPattern          // what triggered commitment
  goal_facia:        GoalDescription          // what "done" looks like

  commitment_ts:     timestamp                // when spawned
  parent_pursuit:    pursuit_id | null        // recursive nesting
  sub_pursuits:      list[pursuit_id]         // children spawned
  actions_taken:     list[engram_activation]  // audit trail through engrams

  completion_test:   Predicate                // evaluable: are we done?
  status:            pending | active | suspended | completed | abandoned
  dopamine_trace:    list[DopamineEvent]      // commitment / subgoal / completion

  metadata:          { priority, inertia, tags }
}
```

### goal_facia
A GoalDescription is a `FACIA`-style structured representation that can be
matched against observed state. It is not a string or a wish — it is a
**predicate that can be evaluated against the current milieu / memory /
external state to answer: are we there yet?**. `completion_test` is
what actually evaluates it; `goal_facia` is the declarative shape of it.

### dopamine_trace
Three event kinds, matching Schultz:
- `DopamineEvent(kind="commitment", ts=…, magnitude=…)` — fires at spawn time.
- `DopamineEvent(kind="subgoal",    ts=…, magnitude=…)` — fires when a sub-Pursuit completes or an intermediate predicate clicks.
- `DopamineEvent(kind="completion", ts=…, magnitude=…)` — fires when
  `completion_test` passes (or at abandonment with negative magnitude).

The trace is *data*, not just logging. Other engrams can trigger on it —
a dopamine ding at commitment can modulate attention, affect milieu,
and prime related Pursuits.

### recursive sub-Pursuits
A Pursuit may spawn sub-Pursuits. A sub-Pursuit carries a pointer to its
parent. When it completes, its completion is a sub-goal dopamine event on
the parent. When the parent's completion test evaluates, it can read
whatever sub-Pursuit outcomes contributed.

This is how "reply to this message" nests inside "address the user's
request" nests inside "tend this conversation thread" — each level gets
its own goal-facia and its own completion test.

---

## 5. What this explains

### The BOREDOM bug (foreman_scan → do-ticket → reply discards progress)

Current flow, without Pursuits:
1. `PROC_BOREDOM_TRIGGER` fires. Action: `foreman_scan` — pick a ticket.
2. Foreman picks `T-xyz`. Action: `do-ticket(T-xyz)` — start work.
3. While work is in flight, user sends a message. Action: `reply` fires.
4. `reply` completes. The in-flight `do-ticket` state is orphaned — no one
   was holding a pointer to it as "the thing we were doing." It does not
   resume. It just... stops.

The problem is at step 1 already: `PROC_BOREDOM_TRIGGER` fired
`foreman_scan` as an action, not as the entry to a sustained pursuit. There
is no object named "Igor committed, at 10:47, to address the boredom signal
by finishing a ticket." So there is nothing for `reply` to suspend and
return to.

With Pursuits:
1. `PROC_BOREDOM_TRIGGER` spawns `Pursuit(name="address_boredom",
   goal_facia=finished_a_ticket)`. Commitment dopamine fires. The Pursuit
   holds across engram firings.
2. The Pursuit spawns sub-Pursuit `Pursuit(name="do_ticket_T-xyz",
   parent=address_boredom)`.
3. `reply` arrives. It spawns its own Pursuit — *also* with the parent set.
   The parent suspends, the reply runs, the parent resumes.
4. `do_ticket_T-xyz` completes. Sub-goal dopamine on parent. Parent
   evaluates completion_test → passed. Completion dopamine.

The behavior is the same engrams, wrapped in commitment trace. The bug
disappears because "what I was doing" is now a first-class object.

### The reply-eats-progress bug
Same structural cause. `reply` in current Igor is a terminal action — it
fires, it speaks, it ends. Wrapping `reply` in a Pursuit (with a goal-facia
"user's request has been addressed") makes it composable with other in-flight
Pursuits: it can pause them, inherit their context, and return control.

---

## 6. Programming pattern: goals are everywhere

Pursuits are not reserved for "big" goals. "Reply to this message" is a
Pursuit. "Close this ticket" is a Pursuit. "Answer this question" is a
Pursuit. The pattern is: **when an action is not an immediate reflex, wrap
it in a Pursuit**.

Signs an action wants a Pursuit wrapper:
- It can be interrupted mid-flight by another stimulus.
- Its "done" state is something other than "action executed" — there is a
  check to run after the act to see if the outcome obtains.
- It may span multiple engram firings.
- Its completion is *interesting to other parts of the system* — something
  elsewhere will want to know when it's done, or get a dopamine ding.
- It may spawn sub-actions that need to know about the parent (so they can
  suspend/resume or report sub-goal completions).

Signs an action does *not* need a Pursuit wrapper:
- It is a single synchronous engram firing whose only outcome is the firing
  itself (e.g. a log write, a metric increment).
- It is a pure stimulus-response reflex with no outcome-sensitivity — the
  point is the reaction, not what the reaction accomplishes.

When in doubt, wrap it. Cheap to add, informative to read, removes a class
of bugs whose root cause is "no one was holding the goal."

---

## 7. Relation to existing Igor subsystems

### Milieu
A Pursuit's commitment_ts and dopamine_trace can feed Milieu directly:
commitment dopamine → arousal/dominance bump, completion dopamine →
valence bump, abandonment → valence down. This replaces ad-hoc
milieu updates from individual engrams with a principled model: affect
follows from goal dynamics.

### Basal Ganglia (lateral inhibition / habit scoring)
BG continues to score and select engrams. Pursuits sit above BG: a Pursuit
does not pick which engram fires next — it declares what it's trying to
accomplish and lets BG run as usual. The Pursuit's role is to *remember
the intent* across the many BG cycles that constitute the work.

### TWM (transient working memory)
Active Pursuits live in TWM. When Igor is asked "what are you doing?", the
answer is read from the stack of active Pursuits. This is also how the
stale-work detector would find "address_boredom committed 47 minutes ago,
no sub-goal dopamine since minute 3" and flag it for attention.

### Goal formation (T-goal-formation-from-conversation, GH#427)
That ticket is about crystallizing conversation threads into *persistent*
goals — the permanent kind, things Igor cares about long-term. Pursuits are
the **transient** kind: one-shot commitments that live from entry to
completion. A persistent goal can spawn Pursuits; a completed Pursuit can
update the evidence for a persistent goal. They compose, but they are
different objects.

### Planning as waypoint graph (T-planning-as-waypoint-graph, GH#428)
That ticket is about building intermediate-waypoint structure between a
goal and the present. Pursuits are the execution side of the same problem:
once the waypoint graph says "go here next," a Pursuit is what actually
carries the intent forward. Planning produces waypoints; Pursuits pursue
them.

---

## 8. What this is not

- **Not a scheduler.** Pursuits do not schedule engrams. BG still selects
  which engram fires. Pursuits only hold the goal state around the selection.
- **Not an interpreter.** There is no "Pursuit runtime" that executes
  anything. The engrams do all the execution. Pursuits carry meta-state.
- **Not a task queue.** The ticket queue is a different object — a list of
  planned work items. Pursuits are in-flight commitments, possibly to
  tickets, possibly to in-conversation asks, possibly to homeostatic drives
  like addressing boredom.
- **Not a replacement for engrams.** If anything, Pursuits make engrams
  *more* load-bearing, because more actions become fire-inside-a-Pursuit.

---

## 9. Open questions (for the implementation tickets)

- Storage: Pursuits in TWM only (ephemeral), or persisted to Postgres like
  engrams? Default guess: TWM while active, Postgres on completion for
  audit and learning.
- Completion test representation: reuse FACIA, or a new predicate
  language? Default guess: FACIA predicates, since they already evaluate
  against structured state.
- Abandonment policy: who decides to abandon a Pursuit, and on what signal?
  Default guess: a timeout + a dopamine-trace staleness check.
- Interaction with worker foreman: does the foreman spawn Pursuits, or do
  Pursuits dispatch to the foreman? Default guess: Pursuits are the outer
  frame, foreman is an engram called from inside them.

These get nailed down in T-single-pursuit-test-case (which forces the
primitives to face real state) and T-pursuit-engram-programming-docs
(which codifies the patterns that survive).

---

## 10. Related

- `engram_language.md` — the layer below Pursuits. Unchanged.
- `subsystem_cognition.md` — BG, Milieu, Thalamus. Pursuits feed Milieu and
  sit above BG.
- `D-pursuit-layer-2026-04-22` — the decision rollup for this layer.
- Tickets: T-single-pursuit-test-case, T-pursuit-engram-programming-docs,
  T-reply-forms-pursuit.
