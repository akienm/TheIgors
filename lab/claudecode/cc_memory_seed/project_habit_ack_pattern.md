---
name: habit_ack_pattern
description: Design note — acknowledgment responses should emerge from habit tree, not hardcoded infrastructure
type: project
---

PROC_THINKING_ACK design note — deferred until after Windows round.

Acknowledgment responses like "Thinking about that..." should emerge from the habit tree on first pass, not be hardcoded in main.py. Current fix (main.py line ~3469) hardcodes the web-facing message — this is a stopgap.

**The pattern**: first pass through tree fires a response habit that emits a lisped acknowledgment when complexity is high and intent is non-interactive. Background job still launches. Second pass delivers the real answer.

**Why:** Same family as "one moment please" (D107). General principle: the tree should handle all user-facing communication; main.py infrastructure should not generate human-facing text directly.

**How to apply:** When implementing, seed PROC_THINKING_ACK as a response habit. Trigger: high-complexity / async-bound queries. Action: emit `_igor_lisp("Thinking about that...")`. Remove the hardcoded branch in main.py.

**Priority**: after Windows round.
