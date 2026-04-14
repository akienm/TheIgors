# stateless by design

**Path:** `theigors/architecture/principles/stateless-by-design`
**Updated:** 2026-04-14T17:28:23.156717 by claude-code

Hot-reloadable modules hold no state. State lives in the DB. This is what makes hot_reload safe and lets Igor pick up code changes without losing his place. If a module needs to remember something across calls, it stores it in memory_palace, a SYSCFG node, or another DB-backed surface.

## Pointers

- `wild_igor/igor/tools/hot_reload.py`
