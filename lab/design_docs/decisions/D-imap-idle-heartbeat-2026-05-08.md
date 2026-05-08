# D-imap-idle-heartbeat-2026-05-08
**title:** IMAP IDLE client + BaseDevice heartbeat = push-based health monitoring
**date:** 2026-05-08
**status:** open
**spawned_tickets:** T-bus-imap-idle-client, T-bus-heartbeat, T-librarian-health-aggregator

## Decision narrative
Two connected decisions: (1) implement IMAP IDLE on the bus client/listener side so all rack participants (Igor, the Librarian, etc.) wake on server push rather than polling — zero CPU at rest, sub-100ms wakeup; RFC 2177 29-min timeout handled with keepalive re-entry. (2) BaseDevice publishes a heartbeat envelope to comms://heartbeat every N seconds (default 30); the Librarian sits in IDLE on that mailbox and maintains a last-seen table — silence for >2N = suspect, >3N = presumed down. This inverts the health monitoring model: aliveness is demonstrated by continuous publication, not answered on query. Complements the existing pull health() interface. Librarian restarts include a 2N warm-up period before silence thresholds activate.
