"""
filesystem.py — T-uc-filesystem-shelf (2026-04-19), partial: re-export shim.

## Status: shim-reversed (same pattern as T-uc-budget-shelf)

The canonical implementation lives at wild_igor/igor/tools/filesystem.py
for this pass. UC path exists so new code can import from
lab.utility_closet.filesystem; full inversion happens when the shared
infrastructure (Tool registry, forensic logger, memory cortex helpers)
migrates to UC too.

## Usage today

    from lab.utility_closet.filesystem import (  # or any public API
        evaluate_threshold_habits,
        sandboxed_read, sandboxed_write,
    )

Works identically to the legacy import path.

## Follow-ups to invert (UC becomes canonical)

- T-uc-registry-move — Tool + registry out of wild_igor.igor.tools
- Same story as budget.py: once registry moves, filesystem's own
  dependencies (Tool, registry, cortex helpers) can be imported natively
  from UC without a circular, and the shim direction flips.

## Related

- T-uc-budget-shelf partial (44db598a, 2026-04-19) — same pattern,
  sibling migration
- T-uc-module-migration-epic (closed) — parent
- T-docs-live-in-code (2026-04-19) — why this docstring is where it is
"""

from wild_igor.igor.tools.filesystem import *  # noqa: F401, F403
