# Swarm port-use audit — 2026-05-05

Deliverable for T-swarm-port-audit. Enumerates all current port bindings on
akiendelllinux (the primary active swarm box as of this date) and maps each
to its proposed UnseenUniversity bus address or flags conflicts. Other swarm
boxes (akienyoga9i, akienyogai7, akienasus, akienpi) are offline or dormant
and not enumerated here — their bindings should be checked when brought up
and confirmed against this template.

---

## Live bindings on akiendelllinux (`ss -tlnp` 2026-05-05)

| Port | Bind address | Service | Process | Notes |
|------|-------------|---------|---------|-------|
| 5432 | 0.0.0.0 + [::] | PostgreSQL | system | Igor DB (`Igor-wild-0001`). External binding — should be confirmed firewall-gated. |
| 6379 | 127.0.0.1 + [::1] | Redis | system | Word-graph performance cache (`IGOR_REDIS_URL` in cortex.py). Localhost-only. |
| 8080 | 0.0.0.0 | UC web server (WebSocket + HTTP) | `lab/claudecode/utility_closet_server.py` | Controlled by `IGOR_UC_PORT` (default 8080). Primary agent platform layer (D335). Chat, WS hub, dashboard, metrics. |
| 8082 | 0.0.0.0 | UC web server (pure HTTP fallback) | `lab/claudecode/utility_closet_server.py` | Controlled by `IGOR_UC_HTTP_PORT` (default 8082). Non-WS fallback for the same UC server. |
| 8384 | 127.0.0.1 | Syncthing web UI | syncthing | Localhost-only. File sync service. Not agent-datacenter-related. |
| 10143 | (IMAP/Dovecot) | UnseenUniversity bus backbone | dovecot | Not shown in ss output because Dovecot binds its own; `imap_server.py` connects to it. Default 10143 (test: in-process stub). This IS the bus — not a service on the bus. |
| 11434 | 0.0.0.0 + [::] | Ollama (LLM inference) | ollama | Local inference backend. Referenced by `devices/inference/device.py` (`_OLLAMA_DEFAULT = "http://127.0.0.1:11434"`). External binding — should confirm firewall gate. |
| 22 | 0.0.0.0 + [::] | SSH | sshd | Standard. Not agent-datacenter-related. |
| 22000 | [::] | Syncthing data transport | syncthing | Cross-machine file sync. Not agent-datacenter-related. |
| 139/445 | 0.0.0.0 + [::] | Samba | smbd | File sharing. Not agent-datacenter-related. |
| 53 | 127.0.0.53 / 192.168.122.1 / 127.0.0.54 | DNS | systemd-resolved / libvirt | System DNS. Not agent-datacenter-related. |
| 631 | 127.0.0.1 / [::1] | CUPS | cupsd | Print server. Localhost-only. Not agent-datacenter-related. |
| 1716 | * | KDE Connect | kdeconnectd | Mobile integration. Not agent-datacenter-related. |
| 50970 | 100.93.75.116 | Tailscale (tailnet) | tailscaled | VPN binding on tailnet address. Cross-box reachability fabric. Not a service on the bus; the fabric *under* cross-box routing. |
| 43883 | 127.0.0.1 | **Unknown** | unidentified | Localhost-only. `lsof`/`fuser` returned no PID (may require sudo or be a kernel socket). **Action: identify before next audit.** |

---

## Mapping to UnseenUniversity bus

| Service | Current binding | Proposed bus address | Device | Status |
|---------|----------------|---------------------|--------|--------|
| PostgreSQL | 0.0.0.0:5432 | `comms://postgres` | `devices/postgres/` | Device exists; comms:// wiring not yet live. |
| Redis | 127.0.0.1:6379 | No bus address needed | n/a | Performance cache only; internal to Igor cognition. Not a bus participant. |
| UC web server | 0.0.0.0:8080/8082 | `comms://utility-closet` or integrated into `web_server` device | `devices/web_server/` (stub) | The UC server IS the human-facing bus face. The `web_server` device stub needs to represent it. |
| Ollama (inference) | 0.0.0.0:11434 | `comms://inference` | `devices/inference/` | Device exists and is production-ready. `comms://igor-wild-0001/inference` in design doc. |
| IMAP bus backbone | (10143 via Dovecot) | This IS the bus | `bus/imap_server.py` | Not a device on the bus; the bus transport itself. No address change needed. |
| SSH | 0.0.0.0:22 | n/a | n/a | Infrastructure, not an agent service. |
| Syncthing | 8384/22000 | n/a | n/a | File sync infrastructure, not an agent service. |
| Samba | 139/445 | n/a | n/a | File sharing infrastructure. |
| Tailscale | 50970 | n/a | n/a | VPN fabric — cross-box transport substrate, not a bus participant. |
| KDE Connect | 1716 | n/a | n/a | Mobile integration, not agent-related. |
| Discord bridge | (not running) | `comms://discord-bot` | `devices/discord_bot/` | Device exists; shim exists. Not currently bound — service not running. |
| Matter shelf | (not running) | `comms://matter-shelf` | TBD | Not running. Not yet a device in unseen_university. Future: home automation shelf. |
| SensorTree | (not running) | `comms://sensor-tree` | TBD | Not running. Not yet a device. Future: sensor aggregation. |

---

## Conflicts and flags

1. **PostgreSQL external binding (5432)**: Binding on 0.0.0.0 means Postgres is reachable from the network. Confirm firewall rule exists (ufw/iptables) that blocks 5432 from external traffic. Tailscale fabric is the intended cross-box path — PG should not be open to the WAN.

2. **Ollama external binding (11434)**: Same issue. Ollama binds all interfaces. Cross-box inference requests should route through `comms://inference` on the bus, not directly to port 11434. Firewall gate recommended.

3. **UC server dual-port (8080 + 8082)**: Two ports for one server creates address ambiguity. Proposed rationalization: 8080 for WebSocket + HTTP (IGOR_UC_PORT), 8082 as plain-HTTP fallback (IGOR_UC_HTTP_PORT). Both should be represented by a single `comms://utility-closet` bus address; the port choice is internal to the device.

4. **Port 43883 unknown**: Localhost-only, unidentified. Low urgency (localhost-scoped) but should be named before T-swarm-identity-layer wires cross-box addressing.

5. **web_server device is a stub**: The UC server is the real web_server face. T-swarm-web-tab-ui depends on this device being real. The stub at `devices/web_server/` needs to be wired to the UC server before tab UI work can begin.

---

## Proposed bus address table (complete)

```
comms://utility-closet      → UC server (8080/8082)
comms://inference            → Ollama (11434)
comms://postgres             → PostgreSQL (5432)
comms://igor-wild-0001       → Igor (IMAP mailbox, no direct TCP port)
comms://CC.0                 → Claude Code (IMAP mailbox)
comms://discord-bot          → Discord bridge (not running)
comms://announce             → Announce protocol mailbox (IMAP)
comms://announce-events      → Announce events mailbox (IMAP)
```

---

## Actions before T-swarm-identity-layer

1. Identify port 43883 (check with sudo lsof or via systemd journal).
2. Confirm firewall gates on 5432 and 11434 (or restrict to 127.0.0.1).
3. Wire `web_server` device stub to UC server so it has a real comms:// address.
4. Check other swarm boxes (yoga9i, yogai7) when online and append their bindings here.
