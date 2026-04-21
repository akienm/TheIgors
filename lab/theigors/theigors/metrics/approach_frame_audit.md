# Approach-frame audit — running count of rules reviewed/reframed

**Path:** `theigors/metrics/approach_frame_audit`
**Updated:** 2026-04-21 by T-approach-frame-sensor-node

Tracks progress of the approach-frame audit across CC palace rules and Igor's memory corpus. Counters live as sibling nodes; history node logs batch updates for sparkline rendering.

Consumers: T-audit-cc-rules-approach-frame (CC rules) and T-igor-self-audit-approach-frame (Igor corpus) each increment counters and append to history after each batch.

revision: 2026-04-21 — initial (T-approach-frame-sensor-node)

