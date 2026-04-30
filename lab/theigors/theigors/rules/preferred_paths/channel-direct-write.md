# channel.py direct write → IMAP bus (when available)

**Path:** `theigors/rules/preferred_paths/channel-direct-write`
**Updated:** 2026-04-29 by cc-sprint

applies_when: plan or diff imports or calls channel.py send/write directly
deprecated: "from lab.claudecode.channel import send" or similar
preferred: IMAP bus message (when bus is live) or cc_inbox.append for CC-directed messages
why: direct channel.py writes bypass the IMAP fanout layer — messages land in one mailbox, not all subscribers; bus ensures delivery to future subscribers too
