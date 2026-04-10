---
name: Reach to biology for design questions
description: When a design question is unclear, the answer is in biology — not CS theory
type: feedback
---

Whenever there's a design question, reach to the biology.

**Why:** The whole architecture is a biological model. CS gives you names for things that already exist in the brain. When we're unsure about a primitive, a mechanism, or how two systems should interact — the brain already solved it. The CS framing is useful for implementation, but biology is the ground truth for what the system should do.

**How to apply:** Before reaching for a CS abstraction (coroutine, message queue, mutex), ask what the biological analog is. yield_to = attention shift. error continuation = pain/avoidance reflex. list iteration = saccadic search. The right name and the right semantics usually follow from the biological framing.
