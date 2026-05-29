# NASA ACTS — Combinatorial Test Generation Research

**Date:** 2026-05-29  
**Ticket:** T-nasa-combinatorics-testing  
**Verdict:** GO (with caveats — see below)

---

## What ACTS Is

ACTS (Automated Combinatorial Testing for Software) is a NIST tool that
generates minimal test suites achieving t-way combinatorial coverage — every
combination of `t` parameter values appears in at least one test case. Result:
20–700× reduction in test set size vs exhaustive coverage, with equivalent
fault detection for interaction faults.

Latest release: ACTS 3.3. Free/public domain, 4,500+ users including Adobe,
IBM, Lockheed Martin. Java .jar; runs on Linux/macOS/Windows with JRE.

---

## Integration with Python/pytest

ACTS is Java-based but integrates via file exchange:
1. Define parameters + constraints in an ACTS config file (`.txt` format)
2. Run `java -jar acts.jar <config> <output.csv>` to generate test cases
3. Load generated cases as `@pytest.mark.parametrize` fixtures

No Python SDK; subprocess + CSV parsing is the standard approach. A thin
`acts_generate.py` wrapper (≤50 lines) covers the integration surface.

---

## Most Relevant Use Case: pe_chain

The pe_chain has ~8 phases each with typed input parameters. ACTS targets
exactly this: define each phase's parameter space + validity constraints,
generate a minimal test matrix covering all 2-way (or 3-way) interaction
combinations. Current pe_chain tests cover individual phases; ACTS would
add cross-phase interaction coverage that's currently absent.

Ticket validation is the second target: ~10 boolean/enum fields, many
interdependencies. ACTS with constraints captures invalid combinations
that currently go untested.

---

## Effort Estimate

| Step | Time |
|------|------|
| Parameter/constraint modeling for pe_chain | 30–60 min |
| CLI wrapper + pytest loader | 1–2 h |
| Initial test run + calibration | 30 min |
| Total | ~3–4 h (M ticket) |

---

## Go/No-Go: GO

**Rationale:** pe_chain phase parameters and ticket validation both match
ACTS's sweet spot. The Java dependency is a minor friction; the integration
pattern is well-understood. No licensing risk.

**Caveats:**
- Success depends on clean parameter modeling; poorly-specified constraints
  reduce coverage benefit without reducing test count.
- Start with pe_chain ticket validation (bounded parameter space) before
  tackling the full 8-phase pipeline.

**Next step if GO:** File `T-acts-pe-chain-integration` (M) — add
`acts_generate.py` wrapper + parametrize ticket validation tests.
