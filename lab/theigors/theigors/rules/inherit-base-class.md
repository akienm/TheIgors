# Inherit base class — every non-library class inherits from IgorBase / AgentBase

**Path:** `theigors/rules/inherit-base-class`
**Updated:** 2026-04-29T17:55:55.489114+00:00 by claude-opus-4-7-T-rule-inherit-base-class

The basemost class IS the logging and introspection layer for both Igor
and the unseen_university. Every non-library class inherits from it. This
rule, currently enforced by the D125 audit check, is canonical: it gives
us logging "as easy as print" via inheritance — no `import logging`, no
separate logger handle, no per-file boilerplate.

Lineage:
- `lab/utility_closet/agent_base.py` defines `AgentBase` — the truly
  basemost class. Provides: `get_name`, `log`, `time_it`, `record_perf`,
  `dump`, `_get_caller`. Use this for shared/utility code that lives
  outside `wild_igor/igor/`.
- `wild_igor/igor/igor_base.py` defines `IgorBase(AgentBase)` — Igor-side
  extension that adds `paths().logs` log_dir and `get_timer()`. Every
  Igor-side class inherits from this.
- UnseenUniversity has its own equivalent that descends from `AgentBase`
  in the same lineage.

What inheritance buys you (no import needed):
- `self.log.info(...)` / `self.log.warning(...)` — instead of `print()`.
- `self.log.get_timer(...)` — perf instrumentation as easy as a context
  manager.
- `self.time_it(...)`, `self.record_perf(...)`, `self.dump(...)` —
  introspection comes for free.

Exemptions (these don't inherit from IgorBase / AgentBase — see
`THIRD_PARTY_BASES` in `lab/claudecode/audit_check_igorbase.py`):
- Pydantic models (`BaseModel`)
- Enums (`Enum`, `IntEnum`, `StrEnum`)
- Abstract base shapes (`ABC`, `Protocol`, `Generic`, `NamedTuple`,
  `TypedDict`)
- `@dataclass`-decorated classes
- Built-in exception types
- Specific third-party client bases (Discord `Client`, `Thread`,
  `Process`, etc.)

Exempt classes still avoid `print()` — when one of these needs logging,
get a logger via the module-level `get_logger()` helper or compose with
an inheriting host class.

Print is reserved for true CLI entrypoints (the script main()), and even
those should also log. Anywhere else, `print()` in code is a smell —
audit-debris and audit-smell catch it.

Existing enforcement:
- `lab/claudecode/audit_check_igorbase.py` walks
  `wild_igor/igor/{cognition,memory,tools,network,brainstem}/` and
  reports non-inheriting class definitions. Registered as the audit check
  `primary-classes-must-inherit-igorbase`.

Filing-time enforcement (forthcoming as audit-precode and audit-ticket
ship):
- audit-ticket: ticket adding a new class declares the inheritance, or
  justifies why a non-inheriting shape is required.
- audit-precode: sprint plan that proposes new class names is verified
  against the inheritance rule before any edit.
- audit-smell: post-write diff scan catches a new class that slipped
  through without inheritance.

revision: 2026-04-29 — promoted from informal/D125-only to first-class
palace rule (T-rule-inherit-base-class).

