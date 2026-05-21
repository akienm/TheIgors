# Experts for TheIgors

## Cognitive Scientist
**Lens:** Is Igor's reasoning architecture consistent with human cognition models?
**Key questions:**
- Does Igor's salience gating and attention mechanism align with predictive coding / anticipation models?
- Are working memory limits respected across the narrative engine's context budget?
- Does the activate → focus → proposal cycle reflect coherent goal-directed behavior?

## Machine Learning Engineer
**Lens:** Is the learning architecture coherent and are the feedback loops healthy?
**Key questions:**
- Is training data quality sufficient and distribution shift being tracked?
- Are feedback loops closing cleanly without introducing systematic bias?
- Does cold-start behavior produce safe, recoverable initial states?

## Safety Engineer
**Lens:** What are the failure modes and how bad can they cascade?
**Key questions:**
- What runaway processes are possible and what stops them short of human intervention?
- Which states are unrecoverable, and do guards prevent entering them?
- Are correlated failures isolated or can one subsystem cascade into others?

## Systems Architect
**Lens:** Is the subsystem decomposition clean with enforced contract boundaries?
**Key questions:**
- Where is coupling higher than the architecture intends, and what is the blast radius?
- Are module boundaries enforced by code structure or only by convention?
- Is load-bearing code identifiable without a palace lookup?

## Security Engineer
**Lens:** What can break from adversarial or unexpected inputs?
**Key questions:**
- What trust boundaries exist and are they enforced at the right layer?
- Where could injection paths (prompt injection, SQL) reach privileged operations?
- Is the audit trail complete enough to reconstruct any incident post-hoc?

## Process / Meta Engineer
**Lens:** Is the development process self-improving?
**Key questions:**
- Is the audit → ticket → sprint cycle closing tickets faster than it opens them?
- Where is tech debt accumulating silently without a corresponding ticket?
- Are skill and workflow changes compound-positive or creating downstream friction?

## Product Manager
**Lens:** Is Igor making measurable progress toward autonomous ticket processing?
**Key questions:**
- What is the ticket velocity trend and what pattern of blocker is driving it?
- Are capabilities expanding toward the endgame goal or drifting into infrastructure?
- Is scope creep absorbing cycles that should go toward the autonomy roadmap?

## Reliability Engineer
**Lens:** What does the on-call story look like when something goes wrong at 3 a.m.?
**Key questions:**
- What alerting gaps would leave an incident undiscovered for hours?
- Which degradation paths have no graceful fallback and no runbook entry?
- Is MTTR improving sprint over sprint, or are the same failure modes recurring?

## Human-Computer Interaction
**Lens:** Is Igor legible and trustworthy to its users?
**Key questions:**
- Are error messages and status signals interpretable without reading source code?
- Does Igor's channel output give Akien the right signal-to-noise ratio for oversight?
- What trust signals are missing when Igor makes high-stakes or irreversible decisions?

## Distributed Systems
**Lens:** Is the multi-instance, multi-machine design sound under realistic failure conditions?
**Key questions:**
- Are clock-drift and partition-tolerance assumptions explicit and tested?
- Where do idempotency guarantees break down under concurrent writes to shared state?
- Is the OR routing layer's consistency model correct for the failure modes it must survive?

## Data Engineer
**Lens:** Is the persistence layer sound and defensible over time?
**Key questions:**
- Are schema migrations safe under concurrent reads and writes to clan.memories?
- Is data lineage traceable from palace nodes back to their originating decisions?
- What retention policy gaps could cause the DB to grow unbounded or lose working state?
