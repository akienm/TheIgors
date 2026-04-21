# Docs live in code — top-of-file docstrings, not DSB/CSB

**Path:** `theigors/rules/docs-live-in-code`
**Updated:** 2026-04-21 by T-palace-rules-versioned

Coding standard (T-docs-live-in-code, 2026-04-19):

- Subsystem docs are top-of-file docstrings on the primary file. Design decisions, architectural intent, which D### decisions shaped the design, and which engrams participate all live here — NOT in separate DSB/CSB files.
- Igor holds the index. A directory-service table/node maps each subsystem to its primary code file(s). Before surgery, CC queries the index → reads the file's top-of-file docstring → then edits.
- Migration pattern: when you touch a load-bearing file, promote its external docs (DSB/CSB/design_docs) into its docstring. Leave the external as a historical log; point from it to the code.
- When Akien explains something twice, it goes into the relevant docstring, not into a separate doc. Bias for inline, against extraction.
- Scope: LOAD-BEARING subsystems (reading, cortex, NE, comms, scope_guard, pe_chain, worker pools, inference gateway). Trivial utilities still follow 'don't comment the obvious.'

Index location: palace path `theigors/subsystem_index`, children map subsystem → primary file.

revision: 2026-04-21 — initial versioned tag (T-palace-rules-versioned)


## Pointers

- **check:** `theigors/rules/ticket_design_checks/docs-in-code`
