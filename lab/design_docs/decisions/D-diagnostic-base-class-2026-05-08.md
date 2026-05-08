# D-diagnostic-base-class-2026-05-08
**title:** Standalone python_diagnostic_base_class micro-package with loguru + tagged logging
**date:** 2026-05-08
**status:** open
**spawned_tickets:** T-python-diagnostic-base-class-repo, T-swadl-add-pyautogui, T-swadl-add-dogtail, T-swadl-add-playwright, T-swadl-readme-interface-libs, T-adc-performance-points, T-swadl-performance-points, T-igor-pypi-tagged-release, T-adc-pypi-tagged-release, T-swadl-pypi-tagged-release

## Decision narrative
Extract shared logging+perf+naming primitive into a standalone pip-installable micro-package (`python_diagnostic_base_class`). Merges SWADL's instance naming (gc.get_referrers, hierarchical get_name, substitution engine, bannerize/dump) with ADC's log path conventions. Uses loguru as the backend with a TaggedLogger proxy: `self.logger.perf('msg')` binds tag via loguru `.bind()`, enabling handler-level routing (e.g. PerformanceHandler writes tag=perf rows to rolling per-day CSV). Convenience shorthands (`self.debug()` etc.) remain. SWADL and ADC both pip-install this; neither imports the other. Also adds SWADL driver coverage (pyautogui, dogtail, playwright) and GitHub Actions PyPI publish pipelines for all three repos.
