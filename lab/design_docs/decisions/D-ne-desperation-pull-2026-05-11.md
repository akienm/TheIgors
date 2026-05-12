# D-ne-desperation-pull-2026-05-11
**title:** NE empty → active LTM desperation kick + faster boredom window
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-ne-desperation-pull-ltm, T-boredom-window-shrink

## Decision narrative
When the narrative engine produces no result, Igor should actively search LTM rather than waiting passively for boredom to accumulate. Sensory deprivation biology model: a starved narrative engine searches harder for material, not slower. Implementation: add MemorySurfacer.force_push() (top-N by activation_score, no keyword requirement, once-per-cycle rate-limit) called from the coa.py NE-empty branch; separately reduce BoredomDetector.WINDOW_MINS 20→5 to make the reactive path faster. Alternative considered: boredom-window-shrink alone (simpler but still reactive, not proactive). Constraint: must not generate infinite LTM churn — force_push guarded to once per NE cycle.
