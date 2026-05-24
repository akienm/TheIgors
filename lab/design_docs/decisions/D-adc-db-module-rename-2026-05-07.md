# D-adc-db-module-rename-2026-05-07
**title:** Rename UnseenUniversity/db.py → db_proxy.py for logger clarity
**date:** 2026-05-07
**status:** open
**spawned_tickets:** T-adc-db-module-rename

## Decision narrative
UnseenUniversity/db.py produces logger name unseen_university.db which reads as a SQLite file reference. Renaming to db_proxy.py clarifies it is a proxy layer (unseen_university.db_proxy). Pure rename — no logic changes.
