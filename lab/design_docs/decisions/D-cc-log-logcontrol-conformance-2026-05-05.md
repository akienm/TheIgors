# D-cc-log-logcontrol-conformance-2026-05-05
**title:** CC chat log ingestion through agent_datacenter LoggingControlCenter interface
**date:** 2026-05-05
**status:** open
**spawned_tickets:** T-cc-log-handler-class, T-cc-log-stop-hook-wire

## Decision narrative
CC's JSONL transcript → markdown pipeline should route through agent_datacenter's logging infrastructure rather than bespoke standalone scripts. The JSONL reader becomes the emitter, and a logging.Handler+Formatter subclass (in devices/claude/chat_log_handler.py) owns the output format. ClaudeDevice implements BaseDevice.logs(). Python logging is pub/sub — consumer formats, producer is format-agnostic. This eliminates the two-formatter mess (export_chat.py vs chat_log_formatter.py) and makes CC a first-class device in the log system. LoggingControlCenter extension NOT in scope — it already names CC.0 in its log tree layout.
