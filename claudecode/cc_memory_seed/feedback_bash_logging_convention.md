---
name: bash-logging-convention
description: All bash scripts in TheIgors use logcmd/logecho pattern from akientools logger_for_bash
type: feedback
---

All bash scripts written for TheIgors must use the `logcmd`/`logecho`/`timestamp()` pattern from `akientools/bin/logger_for_bash`.

For self-contained scripts (new-box setup, sudoer daemon, etc.) that can't depend on akientools being installed: inline the three functions directly.
For scripts that can assume akientools on PATH: source it.

**Why:** Commands that go awry automatically produce a forensic log (timestamp + command + output + result_code) without extra instrumentation. Consistent pattern across all scripts.

**How to apply:** Every bash script gets `logtarget=...`, then either `source logger_for_bash` or inline `timestamp()`/`logecho()`/`logcmd()`. Bare commands are wrapped with `logcmd`. Status messages use `logecho`.
