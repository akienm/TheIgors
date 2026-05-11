# D-dreaming-enhancements-2026-05-11
**title:** Dreaming enhancements — CC /dream command + Hebbian co-activation edge strengthening
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-cc-dream-command, T-dreaming-wg-hebbian

## Decision narrative
Two extensions to the shipped dreaming module (T-igor-dreaming-module): (1) CC-side /dream skill to manually trigger Igor's dreaming module via channel_send — analogous to AutoDream's /dream command, filling the gap between Igor having dreaming and CC having a way to invoke it. (2) Hebbian co-activation strengthening: after synthesis, parse recent clan.traces to find memory node pairs that co-activated 3+ times and UPSERT weight increases into clan.interpretive_edges. Inspired by MIT astrocyte research showing memory capacity scales dramatically faster when a mediating layer strengthens based on co-activation patterns.
