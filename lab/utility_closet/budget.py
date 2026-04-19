"""
budget.py — T-uc-budget-shelf (2026-04-19), partial: re-export from igor/tools/budget.

## Status: shim-reversed (pragmatic compromise)

The intended direction of T-uc-budget-shelf is: implementation lives HERE
(lab/utility_closet/budget.py), and wild_igor/igor/tools/budget.py becomes
a thin re-export shim. That requires budget's dependencies (Tool registry,
DatabaseProxy, forensic_logger) to also live under UC so the UC-side module
can import them without creating a wild_igor ↔ UC circular.

Those migrations haven't happened yet. So for this ticket, we land the
PATH — new code can import from lab.utility_closet.budget — but the
implementation stays in wild_igor/igor/tools/budget.py for now.

Follow-ups to fully invert:
- T-uc-registry-move (Tool + registry → UC)
- T-uc-forensic-logger-move (optional; cross-layer import to igor works for now)

Once registry moves, budget's `from wild_igor.igor.tools.registry import Tool, registry`
flips to `from lab.utility_closet.registry import Tool, registry` and the
circular breaks. Then we invert: implementation here, shim at the old path.

## Usage today

    from lab.utility_closet.budget import budget_status, fetch_openrouter_balance

Works identically to the legacy import path; you're just using the
canonical name. No behavioral difference.
"""

from wild_igor.igor.tools.budget import *  # noqa: F401, F403

# Re-export the names that legacy callers / tests patch on the module.
from wild_igor.igor.tools.budget import (  # noqa: F401
    DatabaseProxy,
    DEFAULT_SPENDING_CAP_USD,
    Tool,
    log_error,
    registry,
)
