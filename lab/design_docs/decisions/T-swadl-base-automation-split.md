# T-swadl-base-automation-split

**Status:** DESIGN — pending Akien review
**Author:** CC (Opus 4.7)
**Date:** 2026-05-02
**Related:** T-web-chat-swadl-regression (consumer)

## Scope / leverage

**Build estimate:** ~2-4 hours (SWADL changes ~1.5h, TheIgors consumer update ~0.5h, verification + tests ~1h). Two repo commits (SWADL + TheIgors).

**Unblocks:** T-gmail-flow-layer (M), T-gmail-login-page-object (M), T-uc-gmail-google (L), T-igor-as-user-epic (XL), T-web-chat-swadl-regression (S, current). Plus any future Igor-as-user / pywinauto / non-test process automation.

---

## Problem

SWADL today conflates two concerns:

1. **Process automation** — driving browsers (Selenium) or OS apps (pywinauto) for non-test purposes (Igor's Gmail flows, web-chat interaction, real product use).
2. **Test running** — pytest/unittest integration, failure logging, accumulated_failures, tearDown reporting.

`SWADLTest` is the only public base class. It inherits `unittest.TestCase` and forces test-machinery on every consumer. Plus, `swadl_cfg.py` auto-spawns a Chrome browser at module-import time (lines 88-95), so **importing any SWADL class spawns a browser**, even if the consumer never intends to drive one (e.g., a test that should skip, or pywinauto-based code that doesn't want Selenium at all).

Concretely surfaced: T-web-chat-swadl-regression Haiku test left orphan browsers because `from SWADL.engine.swadl_base_test import SWADLTest` triggers the cfg-load chain that spawns Chrome — before any skip logic can run.

## Goals

1. **Decouple driver instantiation from module import.** Driver created on first use, not at SWADL config load.
2. **Split `SWADLTest` → `SWADLBaseAutomation` + `SWADLTest`.** BaseAutomation has driver + page/flow plumbing without unittest glue. SWADLTest inherits from BaseAutomation and adds test runner glue.
3. **Preserve driver-interface polymorphism.** Already in place via `SWADLDriver` abstract + `SeleniumDriver`/`PywinautoDriver` adapters. No changes needed here.
4. **Backward compatibility.** Existing tests in `/home/akien/dev/src/swadl/Project/` should still work without source changes.

## Non-goals (separate tickets)

- Adding a working PyWinAutoDriver path end-to-end (stub already exists; activation is its own ticket).
- Refactoring existing /Project/ tests.
- Context-manager API for flows (`with WebChatFlow() as flow: ...`) — worth doing, not now.
- Multi-browser test parallelism.

## Design

### Step 1 — Lazify driver creation (`swadl_cfg.py`)

**Before** (lines 88-95):
```python
try:
    method_key = cfgdict[SELENIUM_BROWSER]
    method_to_call = driver_creators[method_key]
    method_to_call()  # SPAWNS BROWSER AT IMPORT
except Exception as e:
    raise Exception(...)
```

**After**:
```python
def get_driver():
    """Return the active driver, creating it on first call."""
    if cfgdict.get(DRIVER) is None:
        method_key = cfgdict[SELENIUM_BROWSER]
        creator = driver_creators.get(method_key)
        if creator is None:
            raise Exception(
                f"Browser '{method_key}' not yet supported by the framework"
            )
        creator()
    return cfgdict[DRIVER]


def _quit_driver_if_running():
    """Quit and clear the active driver if one was created."""
    driver = cfgdict.get(DRIVER)
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
        cfgdict[DRIVER] = None
```

Importing `swadl_cfg` no longer spawns anything.

### Step 2 — Lazy `driver` and `actions` properties (`swadl_base.py`)

**Before** (lines 87-88, in `SWADLBase.__init__`):
```python
self.driver = self.cfgdict[DRIVER]
self.actions = self.driver.actions
```

**After** (replace with properties — drop these lines from `__init__`):
```python
@property
def driver(self):
    """Lazy access — creates the driver on first reference."""
    from SWADL.engine.swadl_cfg import get_driver
    return get_driver()

@property
def actions(self):
    """Lazy action chains — re-derived each call to stay current."""
    return self.driver.actions
```

**Backward-compat verification:** Only one place assigns `self.driver = ...` (the line we're removing). Verified: zero hits for `self.driver =` in TheIgors (`wild_igor/`, `lab/`, `tests/`). Property pattern preserves all read-side use (`self.driver.find_elements(...)`, `self.driver.get(...)`, `self.driver.save_screenshot(...)`).

### Step 3 — Fix latent `maximize_window` bug (`swadl_base_section.py:93`)

`swadl_base_section.py` line 93 calls `self.driver.maximize_window()` but neither `SeleniumDriver` nor `PywinautoDriver` implements it (this is the `AttributeError("maximize_window")` Haiku caught and worked around). Add to the abstract interface and both adapters:

```python
# In SWADLDriver (abstract):
def maximize_window(self):
    raise NotImplementedError

# In SeleniumDriver:
def maximize_window(self):
    self._driver.maximize_window()

# In PywinautoDriver:
def maximize_window(self):
    raise NotImplementedError  # stub until pywinauto path lands
```

(PywinautoDriver is a stub today — pywinauto isn't installed in the venv. Activating it is a separate ticket; for this design we just keep the interface honest.)

This unblocks the page-section load path (currently broken for everyone, just nobody noticed because the auto-spawn covered for it during dev).

### Step 4 — New class `SWADLBaseAutomation` (new file)

`/home/akien/dev/src/swadl/SWADL/engine/swadl_base_automation.py`:

```python
"""
File: swadl_base_automation.py
Purpose: Base class for non-test process automation (Igor's Gmail flows,
         web-chat interaction, real product use). Provides driver + page/flow
         plumbing without unittest test-runner glue.

Use this when you want SWADL's automation power but you're NOT running a
unittest/pytest test. For tests, use SWADLTest, which inherits from this class
and adds the test-runner machinery.
"""

from SWADL.engine.swadl_base import SWADLBase
from SWADL.engine.swadl_cfg import cfgdict, _quit_driver_if_running
from SWADL.engine.swadl_constants import TEST_DATA, TEST_OBJECT


class SWADLBaseAutomation(SWADLBase):
    """Non-test automation root — driver + plumbing, no unittest glue."""

    accumulated_failures = None

    def __init__(self, name=None, **kwargs):
        # Auto-name from class if not provided — automation roots usually
        # don't need explicit names, unlike page sections.
        if name is None:
            name = self.__class__.__name__
        SWADLBase.__init__(self, name=name, **kwargs)

        # Make this automation root the TEST_OBJECT so accumulated_failures
        # routing in _assertion_post_processor lands on us, not None.
        self.parent = None
        self.accumulated_failures = []
        self.test_data[TEST_OBJECT] = self
        cfgdict[TEST_OBJECT] = self

    def quit(self):
        """Explicit cleanup — quit driver if one was created."""
        _quit_driver_if_running()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
        return False
```

Context manager support (`__enter__`/`__exit__`) lets callers use `with WebChatFlow() as flow: ...` for guaranteed cleanup. Cheap to add now.

### Step 5 — Refactor `SWADLTest` (existing file, slimmed)

`SWADLTest` becomes a thin layer on top of `SWADLBaseAutomation`:

```python
class SWADLTest(unittest.TestCase, SWADLBaseAutomation):
    """Test base — BaseAutomation + unittest test-runner glue."""

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        # Extract test name (existing logic)
        extracted_name = self.__str__()
        parts = extracted_name.split(" ")
        name = parts[1][1:-1]
        cfgdict[TEST_NAME] = name

        SWADLBaseAutomation.__init__(self, name=name)

        # Test-runner reporting setup (FAILURE_LOG, RESULT_LOG)
        cfgdict[FAILURE_LOG] = Output(...)
        cfgdict[RESULT_LOG] = Output(...)

    def setUp(self):
        super().setUp()

    def tearDown(self):
        cfgdict[FAILURE_LOG].close(...)
        cfgdict[RESULT_LOG].close(...)
        super().tearDown()
        self.log.debug(self.bannerize(data=self.cfgdict))
        self.assert_true(exper=len(self.accumulated_failures) == 0)
        self.quit()  # ALWAYS clean up driver, even on test failure
```

Key change: tearDown calls `self.quit()` so test runs no longer leak browsers.

### Step 6 — Consumer updates (TheIgors)

`tests/test_web_chat_swadl_smoke.py` — **Recommendation: keep deferred-import.** Rationale: (a) defends against future regressions in lazy-init (this gotcha cost a session today); (b) documents the trap at the test boundary where readers see it; (c) the smoke test is really operational automation surfacing as a test, so `SWADLBaseAutomation` is conceptually closer than `SWADLTest`. After the SWADL refactor lands, simplify the test to use `SWADLBaseAutomation` directly — still deferred-import, but cleaner.

`wild_igor/tools/swadl_pages/web_chat.py`, `wild_igor/tools/swadl_flows/web_chat.py` — no changes; they use SWADLPageSection / SWADLBaseFlow which inherit from SWADLBase (unchanged interface).

For future Igor-as-user / Gmail flow work: instantiate flows from a `SWADLBaseAutomation` subclass instead of `SWADLTest`, which makes the "not a test" intent explicit.

## Rollout order

1. SWADL repo: lazify driver (Step 1), add lazy properties (Step 2), fix maximize_window (Step 3), commit + push.
2. Verify: import `SWADLTest` in a fresh Python session → no chrome process created. Test by `import SWADL.engine.swadl_base_test; ps aux | grep chrome`.
3. SWADL repo: add SWADLBaseAutomation (Step 4), refactor SWADLTest (Step 5), commit + push.
4. Verify: existing /Project/ tests still pass.
5. TheIgors repo: update test_web_chat_swadl_smoke.py to use SWADLTest pattern (Step 6), commit.
6. Verify: full pytest run leaves zero orphan browsers (`ps aux | grep chrome | wc -l` is 0 after run).

## Test plan

1. **SWADL self-test:** Add a test in SWADL that asserts `import SWADL.engine.swadl_base_test` does not spawn a chrome process. Spawn-detection: `psutil.Process(os.getpid()).children(recursive=True)` filtered for chrome/chromedriver — counts only browsers spawned by the test process, immune to Akien's daily Chrome being open.
2. **TheIgors smoke test:** `python -m pytest tests/test_web_chat_swadl_smoke.py -v` runs and skips cleanly with **zero** orphan browsers (verify post-run with `pgrep chrome | wc -l`).
3. **TheIgors full suite:** `python -m pytest tests/ -x -q` passes (modulo pre-existing T-test-ordering-flakes).
4. **Existing SWADL /Project/ tests:** Run them, verify still pass.

## Open questions for Akien

1. **`accumulated_failures` placement.** Moved to `SWADLBaseAutomation` so non-test automation can also collect non-fatal validation results. Right call, or should it stay test-only?
2. **Auto-quit on tearDown.** Adding `self.quit()` in `SWADLTest.tearDown` means every test kills its browser — no leak, but also no shared session across tests in a class. Verified: existing /Project/demos/google_unit_tests.py and /learning/tests/tests.py are single-method test classes with no cross-test state; default-on quit is safe.
3. **Module-level driver vs per-test driver.** Lazifying means each `get_driver()` call returns the SAME driver (singleton via cfgdict). That's the current behavior. If we want per-test drivers, that's a separate change. Current design preserves the singleton.
4. **Should the smoke test stay deferred-import or switch to SWADLTest?** Recommendation reversed after second-opinion review: keep deferred-import (defends against future lazy-init regressions, documents the trap at the boundary). Will refactor to use `SWADLBaseAutomation` directly once it exists.

## Inertia note

`swadl_base_test.py` and `swadl_cfg.py` are HIGH-inertia within SWADL — only base class, only config bootstrap. You built SWADL; this design needs your stamp before I touch them.

## Risk register

- **Lazy driver could break consumers that import `cfgdict[DRIVER]` directly** (instead of going through `self.driver`). Quick grep of /Project/ + TheIgors to verify nobody does this. If anyone does, they'll get `None` instead of a driver and need to migrate to `get_driver()`.
- **`__init__` ordering in SWADLTest with multiple inheritance** — Python's MRO with `unittest.TestCase` + `SWADLBaseAutomation` can surprise. Will validate by running existing tests; explicit `__init__` calls in the design avoid most issues.
- **Property re-evaluation cost** — `self.actions` was previously a single attribute access; with the property it allocates a new ActionChains each call. Cheap, but if anything captures `self.actions` once and uses it many times, the new behavior allocates more. Audit with grep before commit.
