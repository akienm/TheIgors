# new IGOR_*_ENABLED flag → build to intent + go-live-when ticket

**Path:** `theigors/rules/preferred_paths/feature-flag`
**Updated:** 2026-04-29 by cc-sprint

applies_when: plan or diff introduces a new IGOR_*_ENABLED environment variable gate
deprecated: new feature flag (IGOR_*_ENABLED=false gating new code)
preferred: build the feature directly; file a companion go-live-when ticket that specifies the trip condition for enabling it in prod
why: flags accumulate; each one is a permanent branch in the codebase that needs a documented trip condition or it never ships. Build first, gate only when the go-live condition is non-trivial
