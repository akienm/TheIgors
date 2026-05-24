# devices/akien — Architecture

## What this is

Akien is a human participant in the ADC (Agent DataCenter) rack. This shim
gives his web and Discord traffic a stable comms:// address (`comms://akien/`)
that the bus can route like any other device — without requiring him to run a
daemon or maintain a live process.

## Identity shape

`AkienShim.who_am_i()` returns a dict with this contract:

| Field | Type | Value |
|---|---|---|
| `id` | str | `"akien"` |
| `entity_type` | str | `"human"` — not a daemon or agent |
| `address` | str | `"comms://akien/"` |
| `data_home` | str | `~/.unseen_university/akien/` |
| `channels` | dict | named comms:// sub-addresses (see below) |
| `online` | bool | always `False` — Akien is not a process |

Channels:
- `inbox` → `comms://akien/inbox`
- `outbox` → `comms://akien/outbox`
- `ideas` → `comms://akien/ideas`

The `inbox/`, `outbox/`, and `ideas/` directories exist at
`~/.unseen_university/akien/` and are used by the web server and Discord
transport to queue messages. This shim does not read or write them.

## What this is NOT

- **Not a daemon.** No threads, no process, no lifecycle methods.
- **No comms:// routing.** Wiring `comms://akien/` into the bus is T-web-akien-comms.
- **No TheIgors imports.** This package is stdlib-only so it can be imported
  in any ADC context without pulling in the Igor runtime.

## Extending this device

If you add fields to the identity dict, mirror the change in the test
(`tests/test_akien_device.py`) and update this table. The identity shape
is the contract — downstream code that routes to `comms://akien/` may
depend on these keys.

New device shims should follow the same pattern: one `__init__.py`, one
`shim.py` with a `WhoAmI`-style class and a module-level `who_am_i()`
function, and a `docs/ARCHITECTURE.md` that documents the identity shape.
