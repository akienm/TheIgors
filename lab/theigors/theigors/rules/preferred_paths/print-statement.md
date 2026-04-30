# print() → base-class logger

**Path:** `theigors/rules/preferred_paths/print-statement`
**Updated:** 2026-04-29 by cc-sprint

applies_when: plan or diff adds a print() call inside wild_igor/igor/
deprecated: print()
preferred: self.log.info / self.log.warning / self.log.error (IgorBase logger)
why: print() bypasses log rotation, level filtering, and forensic capture; covered by inherit-base-class rule but listed here for audit-precode quick-check
