# Network area — infrastructure brief

**Path:** `theigors/infrastructure/by_area/network`
**Updated:** 2026-04-29 by cc-sprint

area: network
primary_files: wild_igor/igor/network/
base_classes:
  - IgorBase (wild_igor/igor/brainstem/igor_base.py)
mcp_tools:
  - channel_read, channel_send (cc_channel via MCP — preferred)
proxies:
  - make_local_proxy() — instance schema (twm_observations, pending_replies)
imap_buses: IMAP bus (when live) — preferred over channel.py direct write
channels: cc_channel, web_channel
notes: _post_to_channel() is the in-process convenience wrapper; all outbound messages should prefer the MCP channel_send tool from CC sessions
