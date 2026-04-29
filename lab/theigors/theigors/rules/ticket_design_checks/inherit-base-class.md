# inherit-base-class — new class declares IgorBase / AgentBase inheritance or justifies exempt

**Path:** `theigors/rules/ticket_design_checks/inherit-base-class`
**Updated:** 2026-04-29T17:55:55.489114+00:00 by claude-opus-4-7-T-rule-inherit-base-class

applies_when: |
  ticket adds one or more new classes in `wild_igor/igor/` or
  `lab/utility_closet/`, OR adds new classes intended to provide
  long-lived behavior (workers, services, controllers, helpers with
  state).
check_body: |
  ticket declares the new class inherits from `IgorBase` (Igor-side)
  or `AgentBase` (shared/utility), OR justifies the non-inheriting
  shape (Pydantic model / Enum / ABC / Protocol / dataclass / built-in
  exception subclass / specific third-party base).
failure_message: |
  New class must inherit from IgorBase (Igor code) or AgentBase
  (shared/utility code). The base class IS the logging and
  introspection layer — inheriting gives `self.log`, `self.time_it`,
  `self.record_perf`, `self.dump` for free, no separate logger
  import. If the class fits an exempt category (Pydantic, Enum,
  ABC, Protocol, dataclass — see THIRD_PARTY_BASES in
  lab/claudecode/audit_check_igorbase.py), declare which one.
  See theigors/rules/inherit-base-class.

Narrative source (human-reading): theigors/rules/inherit-base-class

This node is the check shape: /review Mode A (audit-ticket) reads the
YAML above at ticket filing time and verifies tickets positively against
it. When editing behavior, edit the narrative at
theigors/rules/inherit-base-class first, then reflect the change here.

revision: 2026-04-29 — initial filing (T-rule-inherit-base-class)

