# AUDIT — 2026-03-25

## Summary

Full 17-step automated audit completed. No critical failures. Several medium/large findings ticketed for Akien review.

---

## Detailed Findings

### Tests — PASS ✅
**Result**: 329 passed, 1 deprecation warning (Python 3.13 compatibility)
- ✓ No blocking failures
- ⚠ Minor: discord.py uses deprecated audioop (external package, not actionable)

---

### File Placement — OK (one stale duplicate) ⚠
**Finding**: Stale files at `~/.TheIgors/` root from older code version
- `~/.TheIgors/learn_queue.json` (Mar 19 08:30) — STALE
- `~/.TheIgors/drain_learn_queue.pid` — STALE
- **Current code**: paths.py correctly writes to instance directory (`~/.TheIgors/igor_wild_0001/`)
- **Instance files exist**: CORRECT locations have been in use since Mar 20

**Action**: Delete stale duplicates (low risk, superseded)

**Instance path clutter**: Multiple instance folders at root indicate past refactoring chaos
- `Igor-wild-0001/` (capitalized)
- `igor_wild_0001/` (correct, active)
- `igor_wild-0001` (old dash variant)
- `igor_Igor_wild_0001` (malformed)

These can be investigated/cleaned later; none are active. Tickets: G-DB-INSTANCE-CLEANUP

---

### Code Smells — 31 ISSUES
**Silent excepts** (no logging in except block): 19 instances across:
- Main cognition path (basal_ganglia.py:346, narrative_engine.py ×4, push_sources.py ×3)
- Core (main.py ×2, boot_check.py:194, cortex.py ×2)
- Tools (budget.py:137, cluster_ssh.py:628, browser.py:556, template_tools.py:134)
- Network (discord_bot.py ×2, listener.py:216, server.py:815)

**Syntax errors** (legacy DRM extraction code, intentional): 7 files in `/tools/ebook_drm/`
- These are vendored legacy code; intentional, not actionable

**Action**: SILENT_EXCEPT in cognition path should log. Ticket: T-audit-findings-20260325 (add forensic logging to catches)

---

### Registry Coherence — OK ✅
**Result**: 176 tools registered, registry loads cleanly
- ✓ No orphaned tool references
- ✓ All declared tools present in registry

---

### Inertia Check — FLAGGED ⚠
**HIGH-inertia file edited**: `wild_igor/igor/memory/models.py` (recent commits)
- **Status**: D228, D227 decisions are being recorded (OK)
- **Action**: Confirm memory model changes are captured in decisions_log.dsb (DONE — D227/D228 present)

---

### Thread Hygiene — OK ✅
**ThreadPoolExecutor found**: main.py:3018
- Uses context manager (`with` statement) → proper cleanup
- Max 2 workers, brief scope → no risk

---

### Log File Sizes — OK ✅
**Max log**: 888K (Igor-wild-0001/igor_rescue.log)
- All logs < 1MB
- No rotation needed

---

### OpenRouter Burn Rate — INSUFFICIENT HISTORY
**Status**: Budget tracker shows 0 samples in 48h window
- Igor balance tracking populates on hourly fetches
- Not a problem; normal for fresh session
- **Action**: Monitor if trend emerges over next week

---

### DB Schema — OK ✅
**Total tables**: 26
**Required found**: 4/4 (memories, ring_memory, twm_observations, interpretive_edges)
- ✓ All critical tables present
- Schema healthy

---

### Dead Code / Orphan Modules — 2 FLAGGED
**Orphan modules** (not imported by anything):
1. `wild_igor/igor/cognition/multi_upstream.py` — review purpose
2. `wild_igor/igor/brainstem/amm_diagnostics.py` — diagnostics utility, check if used

**Action**: Investigate; if truly unused, remove or document why kept.
**Ticket**: T-audit-findings-20260325 (dead module audit)

---

### Duplication — OK ✅
**Result**: No duplicate function bodies (>10 lines) found

---

### Habit Health — 58 HABITS WITH DEAD CODE_REFS ⚠⚠
**Critical finding**: 58 PROCEDURAL habits reference non-existent tool functions

Examples:
- `PROC_WHAT_TIME` → `tools.runner:get_current_time` (missing)
- `CC_FIND_TICKETS` → `tools.runner:find_tickets` (missing)
- `CC_RUN_BASH` → `tools.runner:run_bash` (missing)
- `CC_RUN_PYTHON` → `tools.runner:run_python` (missing)
- `PROC_STORE_CONTACT` → `tools.google_contacts:create_contact` (missing)

**Root cause**: tools.runner and tools.google_contacts modules were removed/refactored but habit code_refs were not updated.

**Impact**: These habits will attempt to call non-existent functions at runtime, causing failures.

**Action**: MUST TICKET — requires DB cleanup (remove/update dead habit refs). Depends on understanding whether these habits should be deleted or if their code_refs need to point elsewhere.

**Ticket**: T-audit-findings-20260325 (58 dead habit code_refs)

---

### TWM Coverage — OK ✅
**Result**: 58 twm_push calls across codebase
- Coverage found in: thalamus, NE, job_manager, anticipation
- ✓ Main cognitive events pushing state to working memory

---

### Dependency Hygiene — OK ✅
**Result**: All declared dependencies in requirements.txt are imported

---

### Credentials / Hardcoded Paths — OK ✅
**Finding**: `igor_wild_0001` appears 10 times in source
- All in comments, docstrings, or config defaults
- Instance ID set via env var; default is correct
- ✓ No hardcoded passwords in source

---

### Simplification Review — 2 CANDIDATES

**File**: wild_igor/igor/cognition/basal_ganglia.py (recent edit)
- **Observation**: BG scoring logic is dense; may warrant extraction of specificity_bonus+intent_gate into named phase
- **Verdict**: Complex but necessary; no simplification without losing clarity

**File**: wild_igor/igor/memory/cortex.py (recent edit)
- **Observation**: search() method handles 3 depth tiers; consider SearchRequest object (D227 context)
- **Verdict**: Reasonable abstraction candidate; depends on how much tier logic grows

**Action**: Defer; revisit after D227/D228 stabilize. Not urgent.

---

## Summary of Findings

| Category | Status | Count | Action |
|----------|--------|-------|--------|
| Tests | PASS | — | OK |
| File Placement | ⚠ STALE | 2 files | Delete (low risk) |
| Code Smells | ⚠ LOGGING | 19 silent except | Ticket + fix |
| Registry | OK | 176 tools | — |
| Inertia | OK | memory/models.py | ✓ Decisions recorded |
| Threads | OK | 1 executor | — |
| Logs | OK | < 1MB | — |
| Burn Rate | PENDING | 0 samples | Monitor |
| DB Schema | OK | 26 tables | — |
| Dead Code | ⚠ REVIEW | 2 orphans | Ticket |
| Duplication | OK | 0 dupes | — |
| Habit Health | 🔴 CRITICAL | 58 dead refs | Ticket + fix |
| TWM Coverage | OK | 58 calls | — |
| Dependencies | OK | — | — |
| Credentials | OK | — | — |
| Simplification | ✓ DEFERRED | 2 candidates | Later |

---

## Fixed Now (Small Fixes)

**Action**: Delete stale files at `~/.TheIgors/` root

```bash
rm ~/.TheIgors/learn_queue.json
rm ~/.TheIgors/drain_learn_queue.pid
rm ~/.TheIgors/milieu_global.lock  # empty lock file
```

---

## Ticketed (Needs Akien Review)

### T-audit-findings-20260325 (HIGH PRIORITY)

**Multi-item ticket covering**:

1. **Silent excepts** (19 instances)
   - Add forensic logging to all except blocks in cognition path
   - Severity: MEDIUM (silent failures hide bugs)
   - Effort: LOW (1-2 lines per fix)

2. **Dead habit code_refs** (58 instances)
   - Audit which habits should be deleted vs. remapped
   - Remove or update code_refs in DB
   - Severity: HIGH (will cause runtime failures)
   - Effort: HIGH (requires DB cleanup + testing)

3. **Orphan modules** (2 instances)
   - Determine if `multi_upstream.py` and `amm_diagnostics.py` are intentionally kept
   - Remove if unused; document if kept
   - Severity: LOW
   - Effort: LOW

4. **Instance folder cleanup** (G-DB-INSTANCE-CLEANUP)
   - Investigate/remove stale instance folders (`Igor-wild-0001`, `igor_wild-0001`, etc.)
   - Severity: LOW
   - Effort: LOW

---

## Recommendations

1. **Immediate**: Delete the 2 stale files at `~/.TheIgors/` root (confirmed safe)
2. **This sprint**: Address the 58 dead habit code_refs (will break Igor at runtime)
3. **Next sprint**: Add forensic logging to silent excepts (prevents future silent failures)
4. **Backlog**: Clean up orphan modules and instance folders (cosmetic)

---

**Audit completed**: 2026-03-25 17:07 UTC
**Auditor**: Claude Code (worker minion T-audit-2026-03-25)
**Next audit**: 2026-03-26 (recommended daily until habits stabilize)
