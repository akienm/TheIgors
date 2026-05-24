# D-igor-config-paths-audit-2026-05-06
**title:** Audit Igor config/paths/logging — what stays vs. generalizes to datacenter
**date:** 2026-05-06
**status:** closed
**spawned_tickets:** T-igor-config-paths-audit (audit only; no move tickets needed)

## Decision narrative

All 7 files in scope are Igor-specific and should remain in Igor. The patterns
they implement (runtime root, restart guard) are replicated independently in
UnseenUniversity as needed.

## Per-file verdicts

| File | Lines | Verdict | Reasoning |
|---|---|---|---|
| config.py | 126 | **KEEP** | Reads igor.switches.cfg / igor.models.cfg; IGOR_* env vars; Igor-specific config tree |
| paths.py | 275 | **KEEP** | PathManager for ~/.TheIgors/*; IGOR_RUNTIME_ROOT / IGOR_INSTANCE_ID; UnseenUniversity has its own ADC_RUNTIME_ROOT pattern in device.py |
| logging_setup.py | 228 | **KEEP + cleanup** | igor.* logging hierarchy; removed igor.network.* handler (network/ deleted by T-igor-network-remove) |
| boot_check.py | 198 | **KEEP** | Verifies Ollama models at boot; writes to ring memory; NE integration — cognition infrastructure |
| env_sync.py | 397 | **KEEP** | DB-first config sync via SWARM node in memory palace; tightly coupled to Igor's graph |
| restart_guard.py | 82 | **KEEP** | Rate-limits restart.flag triggers; instance_dir paths; pattern could generalize but not worth the move yet |
| first_start.py | 114 | **KEEP** | First-start wizard for Igor setup; prompts instance name / DB host; Igor-specific |

## Changes made in this sprint
- `logging_setup.py`: removed `igor.network` / `network.log` handler (dead since T-igor-network-remove)

## Future consideration
- `restart_guard.py` pattern could become a utility in UnseenUniversity for device restart-loop protection
  (low priority; file a ticket when a device needs it)
