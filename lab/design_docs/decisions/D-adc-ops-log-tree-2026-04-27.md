# D-adc-ops-log-tree-2026-04-27
**title:** central operations log tree + Igor instance home migration to ~/.agent_datacenter/
**date:** 2026-04-27
**status:** open
**spawned_tickets:** T-adc-ops-log-tree, T-adc-console-capture, T-adc-chat-history-migrate, T-adc-instance-home-migration

## Decision narrative

All agent runtime data migrates from ~/.TheIgors/ into a hierarchical ~/.agent_datacenter/ tree. Logs live at ~/.agent_datacenter/logs/<system|comms-channel>/ (CC.0 comms channel = CC chat history, Igor-wild-0001 = Igor subsystem logs). Instance flat files live at ~/.agent_datacenter/Igor-wild-0001/. AGENT_DATACENTER_HOME env var configures the root (default ~/.agent_datacenter/). Console capture via tmux pipe-pane (rolling 7d). Igor's reading library is ~/.agent_datacenter/Igor-wild-0001/library/ — personal reference, not reader-utility state. Hard cutover with symlink safety net during transition window. agentctl init stamps the full tree idempotently.
