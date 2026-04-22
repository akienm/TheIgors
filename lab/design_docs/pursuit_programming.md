# Programming with Pursuits — when to wrap, how to wrap

*Companion to `pursuit_layer.md`. Written for engram authors (Igor-self and
Claude Code both). Updated 2026-04-22.*

This doc answers two questions: **when** should an action be wrapped in a
Pursuit, and **how** do you do it. For the conceptual model, read
`pursuit_layer.md` first.

---

## 1. The goal-is-everywhere principle

A common mistake when reading `pursuit_layer.md` for the first time is to
think Pursuits are for **big** things — "Igor's long-term mission," "ship
the feature," "learn about neuroscience." They are not. They are for
**every** commitment, at every scale.

"Reply to this message" is a Pursuit.
"Close this ticket" is a Pursuit.
"Finish reading this paragraph" is a Pursuit.
"Get the current time" is *not* a Pursuit — no meaningful outcome test.

If you only reach for Pursuits when the goal feels significant, you will
reproduce the bug the layer was built to fix: small actions without
commitment trace getting orphaned when interrupted.

**Rule of thumb:** if you can imagine someone asking "did that work?" after
the action fires, it wants a Pursuit. If the only possible answer is "the
action ran," it doesn't.

---

## 2. Quick reference — wrap or skip

### Wrap in a Pursuit if:
- The action **can be interrupted** mid-flight.
- The action's **done-state** is not just "action returned."
- The action **may span multiple engram firings**.
- **Another part of the system cares** when this completes (something will
  want a dopamine ding, milieu bump, or sub-goal signal).
- The action **may spawn sub-actions** that need parent awareness.
- You'd want to answer "what am I doing?" with this action as the answer.

### Skip the wrapper if:
- The action is a **single synchronous firing** whose outcome is the
  firing itself (log write, metric increment, cache invalidation).
- The action is a **pure reflex** — the *reaction* is the point, not what
  the reaction accomplishes.
- The action is a **pure reader** with no side effects and no spawn —
  `current_time()`, `list_tickets()`, `read_node(id)`.

### When in doubt: wrap it.
A wrapped action that didn't need wrapping costs a commitment+completion
dopamine pair of events and one Pursuit record — bytes. An unwrapped
action that needed wrapping produces a ghost — an in-flight state with
no owner. Cheap mistake vs. expensive mistake; default to cheap.

---

## 3. Minimal Pursuit template

```python
from igor.cognition.pursuits import Pursuit, goal_facia, completion_test

def run_wrapped(stimulus):
    pursuit = Pursuit.spawn(
        name="do_the_thing",
        entry_stimulus=stimulus,
        goal_facia=goal_facia(
            # What does "done" look like? A predicate over observable state.
            lambda state: state.get("the_thing_was_done") is True,
        ),
    )
    try:
        # The actual engram firings happen here. They may span
        # many BG cycles, many engram activations. The Pursuit
        # holds the commitment across all of them.
        do_the_thing_via_engrams(pursuit_id=pursuit.id)
    finally:
        pursuit.evaluate_completion()  # fires completion or abandonment dopamine
```

Three things this template is doing, all load-bearing:

1. **`spawn`** — creates the Pursuit, fires commitment dopamine. This is
   the "I am committing to this" signal that the rest of the system can
   observe and respond to.
2. **`pursuit_id` passed to the engram layer** — so that engrams firing
   inside the Pursuit can log their activations against it, and so that
   a sub-engram can spawn sub-Pursuits with the parent set correctly.
3. **`evaluate_completion`** — fires completion or abandonment dopamine
   based on whether `completion_test` passes. This runs even if the work
   was interrupted, so the system gets a signal either way.

---

## 4. Worked example — reply as a Pursuit

Before (current Igor, buggy):

```python
# reply.py — bare action, no commitment trace
def handle_reply(message):
    response = compose_response(message)
    post_to_channel(response)
    # action complete. nothing else knows what just happened.
```

After (reply wrapped in a Pursuit):

```python
def handle_reply(message, parent_pursuit=None):
    pursuit = Pursuit.spawn(
        name=f"reply_to:{message.id}",
        entry_stimulus=message,
        goal_facia=goal_facia(
            lambda state: state.get(f"replied_to:{message.id}") is True,
        ),
        parent_pursuit=parent_pursuit,  # suspends parent if nested
    )
    try:
        if parent_pursuit:
            parent_pursuit.suspend()
        response = compose_response(message, pursuit_id=pursuit.id)
        post_to_channel(response)
        state.set(f"replied_to:{message.id}", True)
    finally:
        pursuit.evaluate_completion()
        if parent_pursuit:
            parent_pursuit.resume()
```

What changes downstream:
- When a BG-spawned `do_ticket_T-xyz` Pursuit is running and a reply comes
  in, the reply Pursuit gets the ticket Pursuit as its parent, suspends
  it, runs reply, resumes the ticket. The in-flight state is preserved.
- Anything observing Pursuit completions (e.g. a milieu update engram)
  knows the reply finished. Valence nudge on successful reply; negative
  nudge if `replied_to:{id}` never gets set.
- "What are you doing?" queries can walk the active Pursuit stack and
  answer truthfully, including the suspended parent.

---

## 5. Worked example — BOREDOM → ticket work, nested Pursuits

```python
# cognition/boredom_idle.py — with Pursuit wrapping

def on_boredom_trigger():
    address_boredom = Pursuit.spawn(
        name="address_boredom",
        entry_stimulus={"kind": "boredom_trigger", "ts": now()},
        goal_facia=goal_facia(
            lambda state: state.get("recent_ticket_closed_ts", 0) > spawn_ts,
        ),
    )
    try:
        ticket = foreman.pick_ticket(pursuit_id=address_boredom.id)
        if ticket is None:
            return  # finally will fire abandonment dopamine

        do_ticket = Pursuit.spawn(
            name=f"do_ticket:{ticket.id}",
            entry_stimulus={"kind": "ticket_claimed", "ticket_id": ticket.id},
            goal_facia=goal_facia(
                lambda state: state.get(f"ticket_done:{ticket.id}") is True,
            ),
            parent_pursuit=address_boredom,
        )
        try:
            run_ticket_engrams(ticket, pursuit_id=do_ticket.id)
        finally:
            do_ticket.evaluate_completion()
            # sub-goal dopamine on address_boredom if do_ticket completed
    finally:
        address_boredom.evaluate_completion()
```

The nesting matters:

- `address_boredom` is the outer commitment. It doesn't care which ticket
  got done — its completion test is "some ticket got closed after I
  spawned." This is the right abstraction: boredom is addressed by
  *any* productive output.
- `do_ticket` is the inner commitment. It cares about the specific ticket.
- When `do_ticket` completes, sub-goal dopamine fires on `address_boredom`.
- When a reply arrives while `do_ticket` is running, the reply Pursuit
  nests with `do_ticket` as parent. Three-deep stack: address_boredom →
  do_ticket → reply. Each layer suspends its parent and resumes it.

---

## 6. Common mistakes

### Mistake: goal_facia checks internal state, not observable outcome
```python
# WRONG — checks whether the function was called, not whether it worked
goal_facia(lambda state: state.get("do_ticket_called") is True)

# RIGHT — checks the outcome we committed to producing
goal_facia(lambda state: state.get("ticket_done:T-xyz") is True)
```
If the goal_facia is satisfied by "the code ran," the Pursuit has no
outcome-sensitivity and its completion dopamine is noise.

### Mistake: too-granular Pursuits
Wrapping every line of every function in a Pursuit creates a commitment
storm. The Pursuit layer is for **interruptible, outcome-bearing actions**,
not for loop iterations.

### Mistake: forgetting parent_pursuit
A reply that forgets to pass `parent_pursuit` becomes a detached Pursuit.
The in-flight parent still runs, but the parent doesn't know the reply
happened and won't suspend. You get the old bug back.

### Mistake: completion_test never passes
If `completion_test` has no real path to passing, the Pursuit stays open
forever, consumes TWM slots, and eventually triggers the abandonment
timeout with no useful signal. Check the test passes in the happy path
before shipping.

### Mistake: wrapping pure readers
```python
# WRONG — read has no outcome to commit to
Pursuit.spawn(name="read_time", ...)
time = current_time()

# RIGHT — just read
time = current_time()
```
If there is no action and no side effect, there is no goal.

---

## 7. Relationship to Engram grammar

Engrams remain the execution substrate. Nothing in the engram language
(D208) changes. What changes is how engrams are **called into**:

Before: an action engram fires because BG scored it highest. It runs,
it returns, nothing remembers it ran.

After: an action engram fires because BG scored it highest, **and** its
firing is recorded against the currently-active Pursuit (via `pursuit_id`
carried in the basket). On completion, the Pursuit can correlate "my
commitment was X, the engrams that fired were Y, the outcome was Z" —
training signal for future scoring.

BLOOM_INHIBIT at the engram layer is unchanged. Pursuits do not compete
via lateral inhibition (they compose hierarchically). The scheduler-free
property of engrams is preserved: at any moment, zero or more Pursuits are
active, and engrams fire underneath them based on BG + milieu alone.

---

## 8. Debugging Pursuits

### "Why didn't this complete?"
Read the Pursuit's `actions_taken` and `dopamine_trace`:
- Commitment event → spawn recorded.
- No subgoal events → no progress happened inside.
- No completion event → still open or abandoned.

If the trace shows engram firings but no outcome, the completion_test is
probably wrong — engrams did their job, the Pursuit just didn't ask for
the right thing.

### "Why is this Pursuit still open?"
TTL and dopamine-trace staleness feed the abandonment policy. A Pursuit
with commitment + zero dopamine events for longer than the staleness
threshold should abandon and fire negative completion dopamine. If it
doesn't, the staleness check is probably disabled or the TTL is too long.

### "Why did this fire twice?"
Spawning a Pursuit with the same `name` + `entry_stimulus` in the same
window is usually a duplicate-trigger bug upstream. The second spawn
should no-op (or attach to the existing Pursuit as a re-entry), not
create a parallel commitment.

---

## 9. Minimum viable Pursuit implementation

For the first test case (T-single-pursuit-test-case), the minimum is:

- `Pursuit` dataclass with the fields from `pursuit_layer.md` §4.
- `Pursuit.spawn()` — creates record, fires commitment dopamine, returns
  the Pursuit object.
- `pursuit.evaluate_completion()` — runs completion_test, fires completion
  or abandonment dopamine, marks status.
- `pursuit.suspend()` / `pursuit.resume()` — for nesting.
- A TWM slot for active Pursuits, readable by "what am I doing" queries.
- A dopamine-event stream that other engrams can subscribe to.

Everything else (persistence, learning, milieu integration, staleness
abandonment) can be layered on after the first test case proves the
wrapping works.

---

## 10. Related

- `pursuit_layer.md` — the concept, primitives, biology grounding.
- `engram_language.md` — the layer Pursuits sit on top of.
- `subsystem_cognition.md` — BG, Milieu, TWM. Pursuits read/write all three.
- Tickets: T-single-pursuit-test-case (first implementation),
  T-reply-forms-pursuit (first real wrap).
