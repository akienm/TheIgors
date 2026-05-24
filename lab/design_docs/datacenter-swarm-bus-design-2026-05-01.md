# Datacenter swarm bus — design conversation 2026-05-01

**Participants:** Akien + Claude (CC)
**Origin:** /fixit pre-sprint-filter sweep flagged T-swarm-via-home-web-server as design-first. Akien stepped through the design while CC took dictation and reflected back understanding.
**Status:** captured for sprint reference. Not yet ratified as a /decided rollup — meant as a working design baseline that will become a /design block when the ticket sprints.

---

## North Star (Akien architectural framing)

- **Datacenter = the agent-as-pieces.** Capability appliances (inference, web_server, postgres, browser_use, swadl, discord_bot, claude, igor-as-tenant). Each appliance independently debuggable. Substrate reusable across projects.
- **Igor = the master reasoning model.** Just cognition (NE, TWM, milieu, BG, engrams, reasoning_workflow, voice_ab). Runs *on* the datacenter, doesn't *contain* it.
- **Any agent can be built on top.** Igor is one tenant. CC is another. Future agents are more.
- **Migration goal:** move everything we can out of Igor into the datacenter. Igor shrinks to pure cognition.
- **Lab split:**
  - `UnseenUniversity/` = cross-project lab (substrate for any agent)
  - `ClaudeAndAkienWorkshop/` = cross-project workshop tooling and skills
  - `TheIgors/lab/` = Igor-only lab (cognition-specific tooling and design)

This is the foundation for everything below.

---

## One bus, three transports

Every component connects via whichever transport is most ergonomic for what it is and what it's doing. Same data model + verbs underneath; only the surface idiom differs:

| Transport | Best for |
|---|---|
| **MCP** | AI agents in their tool-call-native shape |
| **HTTP** | browsers, dashboards, programmatic clients |
| **IMAP** | async / durable messaging — mailbox semantics, the UnseenUniversity Phase 1 bus |

All three share:
- Device registry (who's up, what they expose)
- Envelope shape (sender, recipient, intent, payload)
- Operations (list devices, send to device, query health, subscribe to events)

A single client may use multiple transports for different purposes — e.g., MCP for "send envelope to peer COA," IMAP for "subscribe to long-running notifications." Same bus, different doors.

This isn't a new bus — it's a multi-protocol facade *on top of* the UnseenUniversity substrate (Phase 1 IMAP, registry, envelope, router). The "home web server" is where the HTTP face terminates.

A 4th transport face, **tmux**, is a special observability shape (see below).

---

## Identities and surfaces

### Identity scheme

- **`<box-name>.<instance-number>`** is the bus address. Examples:
  - `akiendelllinux.1` — first instance on akiendelllinux (the home-DB box)
  - `akiendelllinux.2` — second instance on akiendelllinux (background)
  - `akiendell.1` — first instance on akiendell
- **Lineage name** (e.g., `Igor-wild-0001`) is metadata on the agent identity, not the routing address. Multiple boxes can run instances of the same lineage.
- The existing `comms://igor-wild-0001` URL-style address remains as a lineage-reference; the new `<box>.<n>` form is the primary routing address. Aliasing vs replacement is a small open call at sprint-time.

### Surfaces

An agent has one identity but multiple **surfaces**, each with its own address:

| Surface | Address shape | Idiom |
|---|---|---|
| Console | `comms://cc.0/console` | Terminal/tmux face. Conversational text. |
| MCP | `comms://cc.0/mcp` | Structured tool-call shape. |
| Inference | `comms://igor-wild-0001/inference` | Internal inference channel (bus-only). |
| (default) | `comms://cc.0` | Falls through to the default surface (typically console for interactive agents). |

A message addressed to `comms://cc.0/console` notifies CC on the terminal (shim injects via `tmux send-keys` with attribution). A message to `comms://cc.0/mcp` arrives as a structured tool result / system event.

CC is "kind of a special case" because both surfaces are first-class for it. Igor's primary interactive surface is console; inference is an internal bus surface used by Igor's cognition stack to dispatch inference calls.

---

## Channels

A channel is a **meeting of IMAP inboxes** — a logical room backed by per-participant inboxes that mirror each other.

- Send-to-channel = bus splits the envelope and delivers a copy to each member's inbox.
- Each participant's IMAP inbox is the source for their preferred transport adapter (MCP/HTTP/IMAP) to render the channel.
- The web server's view of a channel is rendered from the unified envelope stream.

### Built-in channels

- **`shared`** — comes with the rack. Always on every box's web server. Has the enter-hook notify-on-mail behavior already wired (this is what wrote yesterday's chat export to `~/.unseen_university/logs/CC.0/`).
- **Per-instance channels** — each interactive surface of each instance can be a channel.
- **Multi-party channels** — e.g., the `igor-cc0` channel where CC and Igor chat over MCP; the bus delivers copies to each, and the web server renders the unified room.

### Visibility model

Default = local. Opt-in for wider exposure.

| Tier | Rule |
|---|---|
| Every box's primary instance (`<box>.1`) | **Always** visible on every web server in the swarm. Mandatory. |
| `shared` | **Always** on every box. Mandatory. |
| Secondary instances (`<box>.2`, `<box>.3`, ...) | **Opt-in.** Each instance individually decides whether to expose, and to which boxes' web servers. |
| Other COAs not exposed | Private to their host box. Bus addressing still works peer-to-peer; just not surfaced in the web UI. |

Example: on akiendell's web server, you'd always see tabs for: `shared`, `akiendell.1`, `akiendelllinux.1`, plus every other box's `.1`. Plus any opted-in secondaries. UI shape: horizontal tabs across the top of the web page, one per channel.

### Notification rule

**Intent-to-address, not ambient stream.**

A channel can have observers (web tabs, listening agents, screen-watchers) — they see the flow but don't get pinged. Notification fires only when an envelope is *addressed to you* specifically.

This separates "watching" from "talking-to" cleanly — exactly the right knob for the everywhere-all-the-time use case to not become noise hell. ACL/mute knobs come later; intent-as-notification-trigger is the foundation.

---

## Multi-COA (per T-concurrent-ne-spawn)

Each COA = NE + TWM + milieu reference, owns its own complete stack:
- Own bus identity
- Own inbox(es)
- Own membership in channels

The box hosts the stacks; the COA owns its stack.

**Within-box concurrency** (multiple COAs per box, ceiling ~4) and **cross-box concurrency** (multiple Igor instances, one per laptop) use the **same mechanism**. A channel between two COAs doesn't care whether they're in the same process, same box, or different boxes. Bus routes over the cheapest available transport; addressing is location-independent.

Cross-box milieu propagation (already shipped, biological partial-isolation) is the same primitive as intra-box milieu propagation (T-concurrent-ne-spawn) — just routed differently underneath.

The swarm is therefore a **flat mesh of COAs** joined into channels. Boxes are scheduling units, not topology units.

---

## Tmux as a 4th transport face (observability shape)

### Bidirectional tmux

- `tmux capture-pane -t <session> -p` — read pane content
- `tmux send-keys -t <session> "text" Enter` — write to pane
- `tmux pipe-pane -t <session> -o 'cat >> /path'` — continuous stream of pane output
- Cross-box: SSH wraps these; same primitives.

Both directions work without ceremony when both processes share the user (CC and Igor both run as akien). Cross-box requires SSH but works the same way.

### The cute trick: agent's CLI session IS a chat channel

Each agent's terminal pane streams through the agent's **shim** (the existing transport adapter in UnseenUniversity). The shim:

- **Outbound:** parses turn boundaries / message events from the stream → emits as channel envelopes onto the bus → web server renders the channel as a tab.
- **Inbound:** takes incoming envelopes from the bus → injects into the agent's session via `tmux send-keys` (with attribution so the agent knows it's not the primary user).

Falls out for free:
- No new chat infrastructure. Reuses tmux + bus + web server. Shim is already the right home for transport translation.
- Every existing CLI session becomes joinable. This conversation right now would be a tab.
- Web users can speak *into* an agent's running session — bidirectional, not just observer mode.

### Source preference per agent

- **Claude Code** has structured transcripts at `~/.claude/projects/<...>/<session>.jsonl` — cleaner than capture-pane (no escape codes, separated turns, explicit tool calls / tool results / timestamps). CC's shim prefers this source.
- **Igor / generic terminal agents** use capture-pane as the source.
- Pattern: shim picks the cleanest available source per agent type; the channel-as-tab UX is identical from the user's perspective.

### Multi-party rendering

When a third party (another Igor, a remote akien on his phone) speaks into CC's channel from the web, the shim injects with attribution:

> **(option a, chosen):** renders as a turn from `igor:` (or whoever) that the agent sees inline and can respond to — multi-party chat shape.

ACL / per-channel mute is deferred; default is option (a) with no filtering until noise actually shows up.

### Observability vs. messaging

Tmux is a different *shape* from MCP/HTTP/IMAP:
- MCP/HTTP/IMAP move **envelopes** (structured messages with sender/recipient/intent/payload).
- Tmux moves **screen state** (raw text-as-it-renders).

Tmux is the observability transport. The cute trick monetizes that by *parsing* screen state into envelopes via the shim — best of both worlds. Screen-as-source, envelopes-as-output.

### Trust / scope consideration

Anything that flashes on screen (an API key in an error message, a token in a debug print) becomes readable to anyone capturing. The trust boundary is already "anything running as akien can read anything else running as akien" — but a routine cross-screen-watch habit makes that boundary much more *active*. A scope rule (shared-screen channels are opt-in per session, like web-channel exposure) addresses this; details deferred to sprint.

---

## Use case summary

**Who uses this and how:**
- **Akien (primary use case):** wants ubiquitous access — both CC and all of Igor's swarm available everywhere all the time. Once remote access is updated, this is the path: open the home web server from anywhere, see the tabs, click to talk to whichever agent on whichever box.
- **Igor:** can also use it (Igor talks to peer Igor on another box; Igor talks to CC) — but secondary use case.
- **Future agents:** any agent built on the datacenter substrate participates the same way.

---

## Existing state

- **Already shipped (UnseenUniversity):**
  - Phase 1: registry, IMAP bus, envelope/router, skeleton, access control, health rollup
  - Phase 2-3: igor + inference + claude devices + YGM nudge pipeline
  - Phase 4: DiscordBot + SWADL + browser-use devices + shims
  - Bus address: `comms://igor-wild-0001` URL-style
  - Default channel: `shared` (with enter-hook notify-on-mail wired)
- **Already shipped (TheIgors/lab/claudecode):**
  - `channel.py` — shared coordination channel for CC sessions and Igor; dual-writes to IMAP `Shared` mailbox; JSONL fallback at `~/.TheIgors/cc_channel/messages.jsonl`
  - `cc_queue.py` — ticket queue with palace canonical store + queue.json echo

- **Not yet there:**
  - The "channel = meeting of IMAP inboxes" multi-party mechanism (logical-room-backed-by-per-participant-inboxes-mirrored)
  - The `<box>.<n>` addressing alias/replacement of `comms://<lineage>`
  - Surfaces as sub-addresses (e.g., `/console`, `/mcp`)
  - Tmux-as-4th-transport-face with shim parsing + injection
  - Web server's tab-per-channel UI for the swarm

---

## What this becomes (sprint-ready outline)

When T-swarm-via-home-web-server sprints, it will produce some combination of:

1. **Identity layer:** `<box>.<n>` addressing with surfaces (`/console`, `/mcp`, `/inference`, ...). Backward-compat alias for existing `comms://<lineage>`.
2. **Channel mechanism:** multi-party-rooms-as-mirrored-inboxes. Send-to-channel splits + delivers; each participant's inbox forwards via their preferred transport.
3. **Visibility rules:** primary-everywhere, secondary-opt-in. `shared` always present. Web UI = horizontal tabs.
4. **Notification rule:** intent-to-address-only, not ambient-stream.
5. **Tmux face:** capture-pane (preferring JSONL transcripts where available) → shim parse → bus envelopes; bus envelopes → shim → `send-keys` with attribution.
6. **Web server tab UI:** rendering channel streams; supporting bidirectional input from the web.
7. **Port-use audit:** enumerate current bindings (UC web server, Discord bridge, Matter shelf, SensorTree, tailnet bindings, CC dashboard) and rationalize them under the unified bus.

The sprint will spawn child tickets per area as scope is locked.

---

## Companion tickets filed today (2026-05-01)

- **T-inference-migrate-igor-to-datacenter-device** (M, claude) — Igor's inference calls go via `comms://inference` envelope. First concrete step of T-capability-extraction-from-igor.
- **T-capability-extraction-from-igor** (XL, epic, claude) — umbrella for the broader move-out-of-Igor effort.
- **T-claudeandakien-workshop-evolution** — updated with cross-project-lab framing (datacenter = cross-project; TheIgors/lab/ = Igor-only).

---

## Open items not resolved here

- Aliasing vs replacement of existing `comms://<lineage>` addresses. (Small design call at sprint.)
- Specific naming for CC's instance numbering vs Igor's (CC.0 with Claude alias; whether CC's full address is `cc.0` or `claude.0` or whatever). Pick at sprint.
- Per-agent ACL / mute / scope rules for who can speak into which surface. Deferred — default is permissive until noise shows up.
- The "remote access we already built but need to update" — Akien noted this exists; needs an update pass to plug into the new web-server tab UI. Possibly a sub-ticket of T-swarm-via-home-web-server.
- Specific port-use audit content — happens at sprint as part of T-swarm-via-home-web-server.

---

*Captured during a long design conversation 2026-05-01. Akien + CC. Reflected understanding back-and-forth across ~10 turns; all "is that clear?" / "did I read that right?" checkpoints hit yes-or-corrected. This document is the snapshot.*
