# D-adc-db-module-rename-2026-05-07
**title:** Rename agent_datacenter/db.py → db_proxy.py for logger clarity
**date:** 2026-05-07
**status:** open
**spawned_tickets:** T-adc-db-module-rename

## Decision narrative
agent_datacenter/db.py produces logger name agent_datacenter.db which reads as a SQLite file reference. Renaming to db_proxy.py clarifies it is a proxy layer (agent_datacenter.db_proxy). Pure rename — no logic changes.
