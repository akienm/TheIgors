---
name: Reading experiments roadmap
description: Eight-experiment roadmap for matrix-based reading without inference engines
type: project
---

The bulk reading / matrix growth work is structured as 8 experiments. We are currently between experiment 3 (done) and experiment 4 (next).

**Experiment 1** (done): Is Akien right that bulk load isn't working? **Answer: YES**

**Experiment 2** (done): Can we observe what's not working? **Answer: YES** (MCP gave deep visibility)

**Experiment 3** (done, post-MCP): With Claude able to work that deeply, can we work through a small piece and achieve the goal of reading without inference engines? **Answer: YES** (POC succeeded)

**Experiment 4** (done): Can we gather enough data about the process of working that out to state: "this is the process, we only need inference for this small bit" — or even better, none at all? **Answer: YES**

**Experiment 5** (done, 2026-03-20): Can we push all that into the matrix and run a small test with queries after the fact on learned material? **Answer: YES**

**Experiment 6** (NEXT): Can we do bulk reading this way?

**Experiment 7**: Can we do bulk reading across the swarm?

**Experiment 8**: What is the load capacity in books of the swarm overnight?

**Why:** T-pipeline-arch and T-swarm-update are both downstream of experiment 4. We can't simplify the inference pipeline without knowing which steps actually require inference. We can't swarm-scale a process we haven't characterized yet.

**How to apply:** When T-pipeline-arch or T-swarm-update come up, redirect to experiment 4 first. The pipeline simplification is evidence-based, not speculative.
