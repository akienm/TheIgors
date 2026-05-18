# D-adc-action-agency-tools-2026-05-13
**title:** Add action and agency tools to ADC as shared infrastructure
**date:** 2026-05-13
**status:** open
**spawned_tickets:** T-adc-action-log, T-adc-file-ticket-tool, T-adc-shell-exec-tool, T-adc-file-rw-tools, T-adc-nighttime-auditor, T-adc-propose-change-tool

## Decision narrative
Add shell_exec, file_read/write, file_ticket, propose_change tools to ADC as shared infrastructure available to all devices (Librarian, Igor, CC). Protection model is machine-level — this machine is dedicated to the Igor project, no path whitelist needed. Postgres for state; filesystem for everything else. All tool invocations append to a structured action_log (adc.action_log); a nighttime auditor reviews the log and posts a daily summary + anomaly report to the shared channel. Gmail integration stays in Igor (Akien wants to walk Igor through that personally). The goal is a three-way conspiracy loop: Librarian notices patterns, files tickets, executes actions; Igor cognates; CC implements.
