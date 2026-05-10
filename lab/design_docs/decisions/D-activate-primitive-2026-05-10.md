# D-activate-primitive-2026-05-10
**title:** Add activate() primitive to Igor's memory tree: distributed decision-making via embedding-based activation, decay, lateral propagation, focus_state persistence, and instance.proposals queue
**date:** 2026-05-10
**status:** open
**spawned_tickets:** T-igor-proposals-queue, T-igor-ne-focus-variable, T-igor-activate-primitive, T-igor-focus-state, T-igor-watch-confidence-accumulator

## Decision narrative
A neuroscience paper on latent variable collapse in cortical decision-making suggested that Igor's memory tree already has the structural substrate for distributed decision-making (WATCH_Q_* = "what does this mean", WATCH_T_* = "what does this mean to me") but lacks: (1) a controlled write channel to clan.memories (dreaming/librarian/playbook should PROPOSE, not directly write), (2) an embedding-based activation primitive that propagates across nodes with decay, (3) cross-cycle focus persistence with hysteresis to prevent thrashing, and (4) evidence accumulation in watch_problems (ramp-to-threshold before surfacing). This decision adds all four. The WATCH_Q → WATCH_T ordering in NE context assembly maps directly to the paper's two-stage latent variable compression. instance.proposals enforces the "Igor decides what goes into clan.memories" architectural principle across all generating modules.
