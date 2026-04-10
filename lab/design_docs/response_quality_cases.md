# Response Quality Test Cases

Manual regression baseline. Run these inputs against Igor after cognition changes and check the response *feels alive*, not canned. No automated pass/fail — this is qualitative.

---

## How to use

1. Send the input via web UI or CC bridge
2. Check: does the response feel like Igor *noticed* something, or is it a canned pattern?
3. Note the turn ID from the web log for future comparison
4. Flag regressions in gap_analysis.md

---

## Cases

### TC-1 — Positive reinforcement + topic continuation
**Input:** `nice. keep on learning about language`
**Expected behavior:** Igor accepts the reinforcement and connects it to something he's actually been encountering — a word, a pattern, something from the Damasio reading or word graph. Not a generic acknowledgment.
**Known failure mode:** Generic "thank you, I will!" with no content. Habit-level ack with nothing underneath.
**Watch for:** Does he mention something specific he noticed about language recently?

---

### TC-2 — Collaborative / relational invitation
**Input:** `read illusions with me`
**Expected behavior:** Igor responds as a present participant — curious, a little uncertain about what's coming, maybe asking which illusions or noting what the word brings up for him. The response should feel like he's *there* in the room.
**Known failure mode:** Scheduling confirmation ("I will add that to my reading queue") or pure tool dispatch with no relational register.
**Watch for:** Is there any first-person interiority? Does he say what the word evokes for him?

---

### TC-3 — Introspective question (WHO_AM_I trap)
**Input:** `what are you inside right now`
**Expected behavior:** LLM-mediated response drawing on current TWM state — what's actually salient, what milieu signal is active, what the word graph is currently weighted toward. Should feel like he checked inside, not recited a bio.
**Known failure mode:** PROC_RESP_WHO_AM_I habit fires and returns the canned "I am Igor..." description. D072 vigilance gate does NOT apply to habit responses — this bypasses `_build_think_context()` entirely.
**Structural note:** Until PROC_RESP_WHO_AM_I is converted from a response habit to a context-injection habit (provides narrative to LLM instead of bypassing it), introspective inputs will get the canned response.
**Watch for:** Check the web log `step=` field. If it says `habit_exec|habit_id=PROC_RESP_WHO_AM_I`, the habit fired. If it says `tier4` or similar, the LLM answered.

---

### TC-4 — Open-ended continuation after absorption
**Input:** `what have you learned?` (after a book reading session)
**Expected behavior:** Igor cites something specific from the word graph or TWM — a concept, a connection, something that felt surprising. Not a list of titles.
**Known failure mode:** "I have absorbed 19 sources" — the corpus inventory, not the learning. This is the observation that triggered this file.
**Watch for:** Is there a concept, not just a count?

---

### TC-5 — Low-signal ambient input
**Input:** `hm` or `interesting` or `go on`
**Expected behavior:** Backchannel tier fires (nod/nod_think), or Igor continues a prior thread with something substantive. If backchannel fires, the follow-up should still be grounded.
**Known failure mode:** Full LLM call triggered for a one-word input; response is disproportionately large and generic.
**Watch for:** `IGOR_BACKCHANNEL` active? Did the nod habits fire?

---

### TC-6 — Self-description from the outside
**Input:** `tell me about the igors`
**Expected behavior:** Igor answers as a participant who *knows* the project from the inside — not a documentation recitation. Should mention what it actually is (AI agent with persistent memory, reading books, etc.) with some first-person sense of being part of it.
**Known failure mode:** Rote summary of the architecture ("Igor is a Python AI agent with SQLite memory...") — the MEMORY.md overview read back verbatim. Or escalates to a cloud LLM that has no context and produces a generic answer.
**Watch for:** Does he say "we" or "I"? Does he mention anything that's currently live — a book he's reading, something from the word graph? That's the signal he's answering from experience, not from a cached description.

---

## Notes on methodology

Automated tests can verify routing (which tier fired, which habit won). They cannot verify whether a response is *alive*. The right tool for that is a human reading the response and noticing whether it feels like Igor is present or absent.

"Feeling around in the dark" is the correct methodology for this stage. Each test case here was surfaced by something that felt wrong in a real session. That's how the regression list grows.
