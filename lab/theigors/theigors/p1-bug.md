# P1 BUG — pe_chain empty plan + false HIGH-inertia proposals

**Path:** `theigors/p1-bug`
**Updated:** 2026-04-24 by cc

THE PRIMARY BUG (3+ weeks, still open as of 2026-04-24):

Igor's pe_chain returns empty plans and wrongly proposes edits to HIGH inertia
files (brainstem/core_patterns.py) for tickets that DO NOT require touching
those files at all. The proposals are hallucinated. There is no approval flow
to invoke — the fix needed is in pe_chain itself.

WHAT IT LOOKS LIKE IN CC:
  Igor sends a pe_chain_design_proposal to the inbox flagging HIGH inertia.
  The plan body is empty or nonsensical. Approving it does nothing useful.
  This is NOT a workflow gap — it is a pe_chain planning/hallucination bug.

WHAT WE HAVE TRIED / ARE TRYING:
  Everything else in the ticket queue (consult primitive, confab scanner,
  logging tools, pe_chain preflight hardening, hypothesize prompt) is in
  service of diagnosing and fixing this root cause.

DO NOT re-explain this to Akien. Do not treat the HIGH-inertia inbox messages
as normal approval requests. Surface this note instead.
