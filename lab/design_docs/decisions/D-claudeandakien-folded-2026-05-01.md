# D-claudeandakien-folded-2026-05-01
**title:** ClaudeAndAkienWorkshop concept obsolete; install-flow + skills + workshop-bound concepts now agent_datacenter material
**date:** 2026-05-01
**status:** open
**spawned_tickets:** T-skills-master-home-in-datacenter, T-claudeandakien-workshop-evolution (closed-as-folded), T-capability-extraction-from-igor (scope-expanded)

## Decision narrative
Akien 2026-05-01: "everything about ClaudeAndAkienWorkshop is an obsolete project. everything about ClaudeAndAkienWorkshop or ClaudeAndAkien repo are now part of agent_datacenter."

Architectural reframe: the boundary becomes **agent_datacenter = substrate + tooling + shared agent infrastructure (skills, install-flow, workshop). Igor = pure cognition.** Anything that crossed machines or was meant to be portable lives in agent_datacenter; Igor is one tenant of the datacenter.

Concrete consequences:
- **Skills home moves out of TheIgors:** "there should be one set of skills outside of ~/.claude kept current for deployment elsewhere inside of agent_datacenter. not in TheIgors anymore." T-skills-master-home-in-datacenter designs the master-source + deploy-to-each-machine pattern.
- **T-claudeandakien-workshop-evolution closed as folded** — its rescoped purpose (skills/tooling docs into agent_datacenter) is now a subset of the datacenter scope.
- **T-capability-extraction-from-igor scope expands** to include cc_skills/ alongside utility_closet/. Coordination: skills home design ships first, then the per-skill triage + moves execute.

Goal Akien stated: "move all this stuff out of igor to simply working ON IGOR."
