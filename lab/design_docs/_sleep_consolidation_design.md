# Sleep Consolidation Honesty — Investigation & Design

**Date:** 2026-05-08  
**Ticket:** T-sleep-consolidation-honesty  
**Chosen path:** A — the Hebbian mechanism already exists; wiring changes are docstring corrections only

---

## What the investigation found

The `_deep_consolidation_pass` in `narrative_engine.py` is documented as "Hebbian wandering
pass over recent search traces" (module docstring line ~44, `consolidation.py` line 111).
The actual implementation does **no Hebbian learning**. It does:

1. TWM observation promotion at 0.5 salience threshold
2. Episodic cluster merge (cosine ≥ 0.80)
3. Weak link pruning (weight < 0.05, last_accessed > 10d)
4. Orphan node adoption (`cortex.adopt_orphans()`)
5. Reading integration (`integrate_reading(batch="50")`)

None of that is Hebbian. It is structural consolidation: promote, merge, prune, adopt.

---

## Where the Hebbian pass actually lives

`SleepConsolidation` (in `cognition/sleep_consolidation.py`, wired as a push source at
`push_sources.py:2918`) is the genuine Hebbian mechanism. It:

1. Gates on quiet period: no conversation for ≥ 10 min
2. Reads `clan.traces` from the last 24 hours
3. Counts co-occurrences: pairs of node IDs that appeared together in ≥ 2 search traces
4. For each qualifying pair:
   - If no edge exists → creates binding at weight `BINDING_WEIGHT * min(coact_count, 5)` (0.08–0.40)
   - If weak edge exists (< STRENGTHEN_CAP = 0.6) → strengthens by `STRENGTHEN_DELTA` (0.05)
5. Pushes TWM observation with salience 0.2 when any edges were created/strengthened

This is replay-based Hebbian: nodes that activate together in search are linked. 
`cortex.reinforce_links()` is the primitive both `SleepConsolidation` and `replay.py` use.

`ConsolidationReplay` (`cognition/replay.py`) is the same pattern for reading: strengthens
edges between FACT_CLOUD nodes deposited in the same reading session (within 120s).

---

## What the gap actually is

The gap is documentation only. The Hebbian claim in the module docstring and `consolidation.py`
points to `_deep_consolidation_pass` (which does not do Hebbian work) instead of
`SleepConsolidation` (which does).

Three places have incorrect or misleading claims:

| File | Line(s) | Wrong claim |
|---|---|---|
| `narrative_engine.py` | ~44: module docstring | "Hebbian wandering pass (_deep_consolidation_pass)" |
| `narrative_engine.py` | ~104: module docstring | "Sleep consolidation (_deep_consolidation_pass, D353)" implies Hebbian |
| `consolidation.py` | ~111 | "_deep_consolidation_pass, D353 — Hebbian wandering" |

---

## Chosen path: A — documentation fix

The Hebbian mechanism (SleepConsolidation) is already implemented, already wired, and
running. No new code is needed. The fix is three docstring edits:

### Change 1: `narrative_engine.py` module docstring (~line 44)

**Before:**  
```
8. Run sleep consolidation pass (_deep_consolidation_pass) during idle
   periods — Hebbian wandering over recent search traces (D353)
```

**After:**  
```
8. Run deep consolidation pass (_deep_consolidation_pass) during idle
   periods — structural: TWM promote, cluster merge, link prune, orphan
   adopt. Separate push source (SleepConsolidation) handles Hebbian
   binding discovery from search traces (D353).
```

### Change 2: `narrative_engine.py` module docstring (~line 104)

**Before:**  
```
Sleep consolidation (_deep_consolidation_pass, D353)
```

**After:**  
```
Offline consolidation (_deep_consolidation_pass): structural maintenance.
Hebbian consolidation (SleepConsolidation push source, D353): binding
discovery from co-activated traces.
```

### Change 3: `consolidation.py` (~line 111)

**Before:**  
```
(_deep_consolidation_pass, D353) during longer idle windows — Hebbian
wandering pass over recent search traces...
```

**After:**  
```
D353 covers two complementary passes:
  _deep_consolidation_pass — structural offline maintenance (promote,
    merge, prune, adopt). Runs when idle >= IGOR_CONSOLIDATION_IDLE_MIN.
  SleepConsolidation push source — Hebbian binding discovery from
    co-activated search traces. Runs when quiet >= 10 min.
```

---

## Optional future (not this ticket)

`_deep_consolidation_pass` could call `sleep_consolidation.push()` as step 6 so the full
consolidation cycle runs together when the deep idle threshold fires. This would mean:
- Structural pass fires at 20 min idle (unchanged)
- Hebbian pass fires alongside instead of waiting for its own 10-min gate

Not required — they already run independently and both gate on idle. File a separate ticket
if the unified pipeline is ever wanted.

---

## What hebbian_bridge.py is

`hebbian_bridge.py` is a back-compat shim re-exporting `coactivation_counter.py` functions.
It is **not** the home for the sleep consolidation Hebbian mechanism. The word-graph
reinforcement it wraps (`reinforce_query_tokens`, `wg_boost_search`) is a separate Hebbian
signal (search-token co-occurrence in the word graph), gated by `IGOR_HEBBIAN_BRIDGE`
(default off). It is orthogonal to the trace-based SleepConsolidation mechanism.

---

## Summary

| Mechanism | Location | Status | Notes |
|---|---|---|---|
| Structural consolidation | `narrative_engine._deep_consolidation_pass` | ✅ Live | Mislabeled as Hebbian |
| Hebbian binding discovery | `sleep_consolidation.SleepConsolidation` | ✅ Live | Correct mechanism, not referenced in NE docstring |
| Reading co-deposit strengthening | `replay.ConsolidationReplay` | ✅ Live | FACT_CLOUD pairs only |
| Word-graph Hebbian | `coactivation_counter` via `hebbian_bridge` | 🟡 Gated off | Independent, different signal |

Path: **A** — docstring corrections in 3 files. No new code.
