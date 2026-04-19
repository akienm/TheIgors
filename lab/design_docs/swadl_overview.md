# SWADL in Igor — Overview

**Source**: github.com/akienm/swadl
**Local checkout**: `/home/akien/dev/src/swadl` (editable install)
**Canonical docs**: see `/home/akien/dev/src/swadl/README.md` and `ENGINE.md`

## What SWADL is for us

SWADL is Akien's test-automation framework. Igor uses it as **hands** — the
bounded action space through which he can interact with browsers and (with
`pywinauto`) Windows apps. It's the deterministic alternative to browser-use:
Igor can only do what the page/section/flow objects model. Drift happens
inside the envelope Akien wrote, not outside it.

## The three-layer model (what Igor needs to internalize)

```
Test / Caller   ── intent: "log into Gmail"
    │
Flow            ── sequence of section calls to achieve that intent
    │
Section         ── how to find and manipulate specific UI elements
                   (selectors live HERE, not in flows)
```

A UI redesign touches sections. Flows and callers stay stable. That
separation is the lesson we want Igor to graph as PAGE_OBJECT / FLOW_OBJECT
nodes (see T-swadl-concepts-in-graph).

## Install

Editable install into Igor's venv:

```bash
~/TheIgors/venv/bin/pip install -e /home/akien/dev/src/swadl
```

Akien edits SWADL in its own repo; Igor sees changes immediately. No vendoring
— one source of truth.

## Import

Python package is uppercase `SWADL`:

```python
from SWADL.engine.swadl_driver import SeleniumDriver, SWADLElement
from SWADL.engine.swadl_base_section import SWADLBaseSection
from SWADL.engine.swadl_base_flow import SWADLBaseFlow
```

## Scope rules (non-negotiable)

- **No account creation** — SWADL flows never sign up new accounts
- **No payment flows** — never modelled, never invoked
- **Only what's explicitly modeled** — if there's no section object for it,
  Igor cannot do it

## Children in progress

- T-swadl-concepts-in-graph — seed PAGE_OBJECT/FLOW_OBJECT/SELECTOR as nodes
- T-gmail-login-page-object — first real artifact (collaborative)
- T-gmail-flow-layer — send/read/archive
- T-igor-manages-own-api-keys — graduation mission
