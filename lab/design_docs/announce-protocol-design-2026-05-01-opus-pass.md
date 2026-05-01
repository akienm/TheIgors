# datacenter-capability-announce protocol — first-pass design (Opus)

**Author:** Claude Code (Opus 4.7, opus-pass)
**Date:** 2026-05-01
**Ticket:** `T-datacenter-capability-announce-protocol`
**Companion:** `lab/design_docs/datacenter-swarm-bus-design-2026-05-01.md`
**Status:** First-pass design for human review by Akien. Not ratified.

---

## 0. TL;DR

The datacenter (skeleton + registry + bus) is the source of truth for what
capabilities exist on a box. Every agent (Igor, CC, future) plugs in via a
small **identity envelope**, the datacenter resolves a static **profile** for
that agent type, intersects profile with the live device registry to produce
a dynamic **manifest**, and ships the manifest back. The agent uses the
manifest to assemble its system prompt (Igor) or its MCP tool surface (CC).

Single transport underneath: **IMAP envelopes on the existing bus**
(`comms://announce/inbox` → reply to agent's mailbox). Surface adapters at
each end translate to whatever idiom is native: Python in
`wild_igor/igor/datacenter_client.py` for Igor, an MCP server in
`agent_datacenter/devices/claude/announce_mcp.py` for CC. This honors the
"one bus, multi-protocol facade" framing in the design doc.

The protocol is **idempotent**, **versioned**, and **push-on-change**:
agents subscribe to a `comms://announce-events` channel and re-pull on
notification.

---

## 1. Existing infrastructure — what we compose, not reinvent

Before designing, an inventory of what already exists in
`/home/akien/dev/src/agent_datacenter/`:

| Capability | Where it lives | What it does |
|---|---|---|
| Per-device descriptor | `agent_datacenter/device.py` lines 17-97 | `BaseDevice.who_am_i() / capabilities() / comms() / requirements()` already returns the data the manifest needs to project |
| Device registry | `skeleton/registry.py` lines 38-115 | Flat-file `~/.agent_datacenter/devices.json`, atomic-write, online/offline/blocked status |
| Skeleton (rack + MCP aggregator) | `agent_datacenter/skeleton/skeleton.py` | Already registers per-device MCP tools dynamically (lines 148-203). Already exposes `rack.devices` / `rack.health` / `rack.channels` MCP tools |
| Bus envelope | `bus/envelope.py` lines 27-62 | Flex-schema `Envelope(from_device, to_device, sent_at, schema_version, payload)` — exactly the shape we need |
| Router | `agent_datacenter/bus/router.py` lines 39-114 | Resolves `comms://<mailbox>` → IMAP `APPEND`, with self-healing relaunch |
| IMAP server | `bus/imap_server.py` | Bus transport layer, mailbox CRUD, IDLE for push |

**Design discipline:** the manifest schema is a **projection** of these
existing dicts, filtered by profile. Don't introduce a parallel data model.

---

## 2. The known router/address inconsistency (must resolve at sprint)

**Real bug, not aspirational:** `router.py:71` (`mailbox = address[len(_SCHEME):]`)
strips only the `comms://` scheme and treats the entire remainder as a flat
mailbox name. But every existing device advertises `comms://<id>/inbox`
(e.g. `IgorDevice.comms() → "comms://igor/inbox"` at `devices/igor/device.py:101`).
The skeleton then registers the bare mailbox `igor` via
`skeleton.py:125` (`self._imap_server.create_mailbox(device_id)`).

So the *advertised* address `comms://igor/inbox` would currently fail
`Router.resolve()` — only `comms://igor` works. The `/inbox` suffix is
documentation, not code. This must be reconciled when the announce protocol
ships, because the design doc proposes `/console`, `/mcp`, `/inference`
sub-addresses as primary surfaces.

**Two forks; pick one:**

| Option | Shape | Pros | Cons |
|---|---|---|---|
| **A. Path-style surfaces** | `comms://cc.0/console`, `comms://cc.0/mcp` | Reads like URL; matches design-doc text verbatim | Router needs a parser change; mailbox naming gets a separator convention |
| **B. Suffix-style surfaces** | `comms://cc.0.console`, `comms://cc.0.mcp` | Zero router change; each surface is just another flat mailbox; matches the existing `cc.0` / `CC.<session>` mailbox pattern | Loses the "single agent, multiple doors" URL aesthetic |

**Recommendation: B (suffix-style).** Justifications:

1. `ClaudeDevice` already does this — `CC.0` is global, `CC.<session>` is
   per-session, both are flat mailboxes (`devices/claude/constants.py`).
   Surfaces are just more of the same.
2. Each surface mailbox can have its own retention, ACL, and IDLE
   subscribers without router changes.
3. Path-style is recoverable later as syntactic sugar in a higher-level
   client (e.g., `comms_url("cc.0", surface="console")` constructs `cc.0.console`).
4. Avoids breaking the router's "comms:// → flat mailbox" invariant, which
   the IMAP IDLE pub/sub design depends on (`router.py:7-9`).

Path-style wins only if Akien explicitly wants URL-aesthetic primary;
mark this as an open question (§ 11.B).

---

## 3. Identity envelope — how an agent plugs in

### 3.1 Shape

The identity envelope is a payload wrapped in the existing `Envelope`
dataclass, sent to `comms://announce/inbox` (a new announce-broker mailbox
the skeleton creates at boot). Mandatory fields below; extra keys allowed
(flex-schema).

```python
# agent_datacenter/announce/envelope.py
from dataclasses import dataclass, field

ANNOUNCE_SCHEMA_VERSION = "1.0"
ANNOUNCE_MAILBOX = "announce"  # comms://announce

@dataclass
class IdentityEnvelope:
    # ── Mandatory ──────────────────────────────────────────────────────
    agent_id: str            # logical type+lineage, e.g. "igor", "cc", "research-orca"
    instance: str            # this-process identifier, e.g. "wild-0001", "session-abc123"
    box: str                 # hostname, e.g. "akiendelllinux"
    box_n: int               # instance number on this box (1, 2, ...)
    pid: int                 # OS pid for liveness debugging
    interface_version: str   # "1.0" — matches BaseDevice.INTERFACE_VERSION
    announce_schema: str = ANNOUNCE_SCHEMA_VERSION

    # ── Optional but strongly encouraged ────────────────────────────────
    lineage: str = ""        # e.g. "Igor-wild-0001" (legacy comms:// form, metadata only)
    coa_id: str = ""         # for cognition-bearing agents with multiple COAs
    surfaces: list[str] = field(default_factory=list)   # ["console", "mcp", "inference"]
    declared_capabilities: list[str] = field(default_factory=list)
                             # what the agent CLAIMS to do; informational only
    proof: dict = field(default_factory=dict)           # see §3.3
```

### 3.2 The bus address derivation

From the envelope, the announce broker computes the agent's primary
mailbox(es):

```
primary       = f"{box}.{box_n}"                        # akiendelllinux.1
surface_mbox  = f"{box}.{box_n}.{surface}"              # akiendelllinux.1.console
coa_mbox      = f"{box}.{box_n}.{coa_id}"               # akiendelllinux.1.coa-2
```

**Mailbox separator convention (locked):** dot (`.`) is the **only**
separator at the IMAP layer. All segments concatenate flat — IMAP sees
`akiendelllinux.1.console.session-7f3a` as one opaque mailbox name. No
parsing of segments at the router level. Higher-level clients
(announce-broker, system-prompt builder) MAY split on dots for display,
but the bus does not. This keeps the router's "comms:// → flat mailbox"
invariant clean.

Lineage form (`comms://igor-wild-0001`) is **kept as alias** for the primary
inbox during transition — see § 8.A.

### 3.3 Identity proofs (for v1: trust by locality)

The trust boundary today is "anything running as `akien` can reach
anything else running as `akien`" — see `datacenter-swarm-bus-design-2026-05-01.md:175-176`.
v1 proof is therefore minimal:

| Proof field | Purpose | v1 verification |
|---|---|---|
| `proof.uid` | Unix uid of the announcing process | **Self-attested** — IMAP is TCP localhost, no SCM_CREDENTIALS path to verify the announcer's actual uid. Skeleton can compare against its own uid as a sanity check, but cannot enforce. v1 is honor-system. |
| `proof.local_socket_path` | Optional: agent listens here, broker pings to confirm liveness | Skeleton attempts a connect — pass on first byte echo. This is genuine verification, but optional. |
| `proof.shared_secret` | Optional, future | Reserved for cross-box federation (Phase 5+) |

**Honest framing:** v1 is "if you can write to the announce mailbox over the
local IMAP, you are who you say you are." That's self-attestation, not
verification. Matches the existing `Skeleton._check_caller_auth` model
(`skeleton.py:205-222`) — envelope-level trust, cryptographic ACL deferred.
The `proof.uid` field is included for forward-compat (future SCM_CREDENTIALS
or token-based verification can populate it meaningfully).

### 3.4 Concrete examples

**Igor plugging in:**

```json
{
  "agent_id": "igor",
  "instance": "wild-0001",
  "box": "akiendelllinux",
  "box_n": 1,
  "pid": 47213,
  "interface_version": "1.0",
  "announce_schema": "1.0",
  "lineage": "Igor-wild-0001",
  "coa_id": "primary",
  "surfaces": ["console", "inference"],
  "declared_capabilities": ["cognition", "memory_palace_owner"],
  "proof": {"uid": 1000}
}
```

**CC plugging in:**

```json
{
  "agent_id": "cc",
  "instance": "session-7f3a",
  "box": "akiendelllinux",
  "box_n": 1,
  "pid": 51188,
  "interface_version": "1.0",
  "announce_schema": "1.0",
  "surfaces": ["mcp", "console"],
  "declared_capabilities": ["editor", "shell"],
  "proof": {"uid": 1000}
}
```

**A hypothetical research agent:**

```json
{
  "agent_id": "research-orca",
  "instance": "literature-sweep-2026-05-01",
  "box": "akiendelllinux",
  "box_n": 2,
  "pid": 60112,
  "interface_version": "1.0",
  "announce_schema": "1.0",
  "surfaces": ["mcp"],
  "declared_capabilities": ["paper_summarize", "arxiv_search"],
  "proof": {"uid": 1000}
}
```

---

## 4. Profile schema — static capability declaration

### 4.1 Definitional split (load-bearing)

| Concept | Lives where | Edited by | Lifetime | Per |
|---|---|---|---|---|
| **Profile** | `~/.agent_datacenter/profiles/<agent_id>.yaml` | Humans (committed under `agent_datacenter/config/profiles/` and synced to the runtime dir on install) | Days–months | Agent **type** (igor, cc, research-*) |
| **Manifest** | Computed per-announce, never persisted long-term | Generated by `ManifestAssembler` | Per-announce (re-derived on change) | Agent **instance** |

Profile is the **what an agent of this type is allowed to see and do**.
Manifest is the **what's currently bound for this instance, given live
state and ACL**. The profile is the contract; the manifest is the runtime
projection.

### 4.2 Why YAML on disk, not Postgres

Same logic as `skeleton/registry.py:6-8`: the skeleton can't depend on
Postgres for its own state, because the Postgres device may itself be down
when the skeleton needs to answer an announce. Profiles must be readable
without the rack being fully up. A YAML file in
`~/.agent_datacenter/profiles/` solves it; atomic-write keeps it safe
under concurrent edit (mirroring `DeviceRegistry._atomic_write`,
`registry.py:103-106`).

### 4.3 Profile YAML schema

```yaml
# ~/.agent_datacenter/profiles/igor.yaml
profile_version: "1.0"
agent_type: igor
description: "Master cognition tenant — full access to inference, memory, web, browser_use"
inherits: []                  # future: profile inheritance ("cc-base" etc.)

# What devices this agent type may bind to. "*" = any registered device.
# Wildcards supported: "inference.*", "*-readonly".
allowed_devices:
  - inference
  - postgres
  - browser_use
  - swadl
  - discord_bot
  - web_server

# Per-device permission overlay — defaults to read_write if device allows.
device_permissions:
  postgres:
    mode: read_write
    schema_filter: ["clan", "memory_palace"]    # optional, devices may ignore
  inference:
    mode: read_write
    rate_limit_per_min: 60
  discord_bot:
    mode: write_only

# Channels this agent type joins by default. The manifest will list these
# resolved against current channel registry.
default_channels:
  - shared
  - igor-cc

# State references — only populated for cognition-bearing agents.
# Tells Igor where its TWM/NE/milieu live so it can reattach after restart.
state_refs:
  twm: "postgres://igor:choose_a_password@127.0.0.1/Igor-wild-0001#twm"
  ne:  "postgres://igor:choose_a_password@127.0.0.1/Igor-wild-0001#narrative_engine"
  milieu: "postgres://igor:choose_a_password@127.0.0.1/Igor-wild-0001#milieu_state"

# Permissions: who can speak to me, who I can speak to.
acl:
  inbound:
    allow: ["*"]              # anyone may send to igor
    deny: []
  outbound:
    allow: ["*"]
    deny: []

# Surface support — which surfaces this profile activates by default.
surfaces:
  console: true
  inference: true
  mcp: false                  # Igor doesn't expose MCP today
```

```yaml
# ~/.agent_datacenter/profiles/cc.yaml
profile_version: "1.0"
agent_type: cc
description: "Claude Code session — inference + channels + memory-read + workshop tooling"
inherits: []

allowed_devices:
  - inference                 # for routed inference; CC's own auth via Max stays untouched
  - postgres                  # palace memory access (READ — see device_permissions)
  - browser_use               # web reads
  - swadl                     # workshop SWADL device for cross-project skill ops

device_permissions:
  postgres:
    mode: read_write          # CC writes tickets, slates, decision rollups today; Igor writes its own cognition state. (See § 11.K — proposed tightening to read_only is an open question, not a v1 default.)
    schema_filter: ["memory_palace", "clan"]
  inference:
    mode: read_only           # CC's own inference path is its Max auth — this is for tool-use
  browser_use:
    mode: read_write
  swadl:
    mode: read_write

default_channels:
  - shared
  - igor-cc

# CC has no cognition state; no state_refs.

acl:
  inbound:
    allow: ["igor", "skeleton", "akien"]
    deny: []
  outbound:
    allow: ["*"]
    deny: []

surfaces:
  console: true
  mcp: true                   # CC's primary tool surface
  inference: false
```

```yaml
# ~/.agent_datacenter/profiles/research-orca.yaml
profile_version: "1.0"
agent_type: research-orca
description: "Literature-sweep research agent — narrow read access, no state"
inherits: ["cc"]              # future: inherit channels + base ACL from cc

allowed_devices:
  - browser_use
  - postgres                  # read-only, narrow
  - inference

device_permissions:
  postgres:
    mode: read_only
    schema_filter: ["public.papers"]
  browser_use:
    mode: read_only           # may fetch; may not POST
  inference:
    mode: read_only

default_channels:
  - shared

acl:
  inbound:
    allow: ["akien", "skeleton"]
    deny: ["*"]               # research agents are not addressable by other agents
  outbound:
    allow: ["postgres", "browser_use", "inference", "shared"]
    deny: ["*"]

surfaces:
  mcp: true
  console: false
  inference: false
```

### 4.4 Profile resolution

```python
# agent_datacenter/announce/profile.py
from pathlib import Path
import yaml

PROFILES_DIR = Path("~/.agent_datacenter/profiles").expanduser()

class ProfileNotFound(Exception): pass

def load_profile(agent_id: str) -> dict:
    """Load profile, applying `inherits` chain. Atomic-read, fails closed."""
    path = PROFILES_DIR / f"{agent_id}.yaml"
    if not path.exists():
        raise ProfileNotFound(f"No profile for agent_id={agent_id!r} at {path}")
    profile = yaml.safe_load(path.read_text())
    for parent in profile.get("inherits", []):
        parent_p = load_profile(parent)
        profile = _merge_profiles(parent_p, profile)  # child overrides parent
    return profile
```

Inheritance is a **future** capability — v1 ships with `inherits: []`
mandatory and the merge function as a TODO. Flagged as open question
(§ 11.C).

---

## 5. Manifest schema — what the datacenter announces back

### 5.1 Top-level shape

```python
# agent_datacenter/announce/manifest.py
from dataclasses import dataclass, field

MANIFEST_SCHEMA_VERSION = "1.0"

@dataclass
class ToolBinding:
    name: str                     # MCP-style tool name, e.g. "inference.complete"
    address: str                  # comms:// address for routing, e.g. "comms://inference"
    interface: str                # one of "mcp", "imap_envelope", "http", "python_callable"
    input_schema: dict            # JSON Schema for the tool's input
    output_schema: dict | None    # JSON Schema for the tool's output (optional)
    permission_mode: str          # "read_only" | "write_only" | "read_write"
    rate_limit_per_min: int | None = None
    description: str = ""

@dataclass
class ChannelSubscription:
    name: str                     # "shared", "igor-cc"
    address: str                  # "comms://shared"
    role: str                     # "member" | "observer" — only members get notifies on intent-addressed
    notify_on_intent: bool = True

@dataclass
class StateRef:
    name: str                     # "twm", "ne", "milieu"
    uri: str                      # e.g. postgres://...#twm or file://...
    mode: str                     # "read_only" | "read_write"

@dataclass
class ACL:
    inbound_allow: list[str]
    inbound_deny: list[str]
    outbound_allow: list[str]
    outbound_deny: list[str]

@dataclass
class Manifest:
    schema_version: str
    issued_at: str                # ISO 8601 UTC
    issued_by: str                # "skeleton@akiendelllinux.1"
    issued_to: dict               # echo of IdentityEnvelope (instance + box + agent_id)
    manifest_id: str              # uuid4 — for idempotence checks on re-announce
    expires_at: str | None        # optional TTL; None = until next push event

    tools: list[ToolBinding]
    subscriptions: list[ChannelSubscription]
    state_refs: list[StateRef]
    acl: ACL

    surface_addresses: dict       # {"console": "comms://akiendelllinux.1.console", ...}
    primary_address: str          # "comms://akiendelllinux.1"

    # Diagnostic / advisory — not load-bearing
    profile_version: str
    profile_etag: str             # SHA-256 of the profile YAML, for cache-validation
    registry_etag: str            # SHA-256 of the relevant registry slice
```

### 5.2 Concrete Igor manifest

```json
{
  "schema_version": "1.0",
  "issued_at": "2026-05-01T18:24:11Z",
  "issued_by": "skeleton@akiendelllinux.1",
  "issued_to": {
    "agent_id": "igor",
    "instance": "wild-0001",
    "box": "akiendelllinux",
    "box_n": 1
  },
  "manifest_id": "9c8a4f1e-2b3d-4e5f-9a1c-7d6e8f9a0b1c",
  "expires_at": null,
  "tools": [
    {
      "name": "inference.complete",
      "address": "comms://inference",
      "interface": "imap_envelope",
      "input_schema": {
        "type": "object",
        "properties": {
          "model": {"type": "string"},
          "messages": {"type": "array"},
          "max_tokens": {"type": "integer"}
        },
        "required": ["messages"]
      },
      "output_schema": {
        "type": "object",
        "properties": {"text": {"type": "string"}, "tokens_used": {"type": "integer"}}
      },
      "permission_mode": "read_write",
      "rate_limit_per_min": 60,
      "description": "Run an LLM completion via the registered inference device."
    },
    {
      "name": "memory.palace_get",
      "address": "comms://postgres",
      "interface": "imap_envelope",
      "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
      "output_schema": {"type": "object"},
      "permission_mode": "read_write",
      "description": "Read or write a memory_palace node by path."
    },
    {
      "name": "browser_use.fetch",
      "address": "comms://browser_use",
      "interface": "imap_envelope",
      "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
      "permission_mode": "read_write"
    }
  ],
  "subscriptions": [
    {"name": "shared", "address": "comms://shared", "role": "member", "notify_on_intent": true},
    {"name": "igor-cc", "address": "comms://igor-cc", "role": "member", "notify_on_intent": true}
  ],
  "state_refs": [
    {"name": "twm", "uri": "postgres://igor:choose_a_password@127.0.0.1/Igor-wild-0001#twm", "mode": "read_write"},
    {"name": "ne",  "uri": "postgres://igor:choose_a_password@127.0.0.1/Igor-wild-0001#narrative_engine", "mode": "read_write"},
    {"name": "milieu", "uri": "postgres://igor:choose_a_password@127.0.0.1/Igor-wild-0001#milieu_state", "mode": "read_write"}
  ],
  "acl": {
    "inbound_allow": ["*"], "inbound_deny": [],
    "outbound_allow": ["*"], "outbound_deny": []
  },
  "surface_addresses": {
    "console":   "comms://akiendelllinux.1.console",
    "inference": "comms://akiendelllinux.1.inference"
  },
  "primary_address": "comms://akiendelllinux.1",
  "profile_version": "1.0",
  "profile_etag": "sha256:7c3a...d0",
  "registry_etag": "sha256:9b1e...44"
}
```

### 5.3 Concrete CC manifest

```json
{
  "schema_version": "1.0",
  "issued_at": "2026-05-01T18:24:32Z",
  "issued_by": "skeleton@akiendelllinux.1",
  "issued_to": {
    "agent_id": "cc",
    "instance": "session-7f3a",
    "box": "akiendelllinux",
    "box_n": 1
  },
  "manifest_id": "1a2b3c4d-5e6f-7a8b-9c0d-e1f2a3b4c5d6",
  "expires_at": null,
  "tools": [
    {
      "name": "memory.palace_get",
      "address": "comms://postgres",
      "interface": "mcp",
      "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
      "permission_mode": "read_write",
      "description": "Read or write a memory_palace node by path. CC writes tickets / slates / decisions today; restriction to read-only would require migrating those write paths first (see § 11.K)."
    },
    {
      "name": "channel.read",
      "address": "comms://shared",
      "interface": "mcp",
      "input_schema": {"type": "object", "properties": {"n": {"type": "integer"}}},
      "permission_mode": "read_only",
      "description": "Read last N messages from a channel."
    },
    {
      "name": "channel.post",
      "address": "comms://shared",
      "interface": "mcp",
      "input_schema": {"type": "object", "properties": {"content": {"type": "string"}, "to": {"type": "string"}}},
      "permission_mode": "write_only"
    },
    {
      "name": "browser_use.fetch",
      "address": "comms://browser_use",
      "interface": "mcp",
      "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
      "permission_mode": "read_write"
    },
    {
      "name": "swadl.run_skill",
      "address": "comms://swadl",
      "interface": "mcp",
      "input_schema": {"type": "object", "properties": {"skill": {"type": "string"}, "args": {}}},
      "permission_mode": "read_write"
    }
  ],
  "subscriptions": [
    {"name": "shared", "address": "comms://shared", "role": "member", "notify_on_intent": true},
    {"name": "igor-cc", "address": "comms://igor-cc", "role": "member", "notify_on_intent": true}
  ],
  "state_refs": [],
  "acl": {
    "inbound_allow": ["igor", "skeleton", "akien"], "inbound_deny": [],
    "outbound_allow": ["*"], "outbound_deny": []
  },
  "surface_addresses": {
    "console": "comms://akiendelllinux.1.console.session-7f3a",
    "mcp":     "comms://akiendelllinux.1.mcp.session-7f3a"
  },
  "primary_address": "comms://akiendelllinux.1.session-7f3a",
  "profile_version": "1.0",
  "profile_etag": "sha256:a1b2...44",
  "registry_etag": "sha256:9b1e...44"
}
```

Note: tools that resolve to the *same* device address (e.g.
`memory.palace_get` and `memory.palace_search`) differ in their MCP tool
name (so CC sees them as separate tools), but route to the same `comms://`
address with different `payload.intent` values. The interface translation
(MCP tool name → envelope intent keyword) is handled by the announce-side
adapter (§ 7).

---

## 6. RPC mechanism — recommendation: IMAP envelopes

### 6.1 Decision: announce flows over the bus, surface adapters at each end

```
┌──────────────────────────┐     IMAP APPEND     ┌──────────────────────┐
│ Igor (datacenter_client) │────comms://announce──▶│ AnnounceBroker       │
│                          │◀───comms://igor──────│ (skeleton subdevice)  │
└──────────────────────────┘   manifest envelope  └──────────────────────┘
            ▲                                              │
            │ Python dataclass                             ▼
            │                                  reads ProfileStore + DeviceRegistry
            │                                              │
            ▼                                              │
   build_system_prompt(manifest)                           │
                                                           │
┌──────────────────────────┐     IMAP APPEND               │
│ CC AnnounceMCP server    │────comms://announce───────────┘
│ (devices/claude/         │◀───comms://cc.<sess>──────────
│  announce_mcp.py)        │   manifest envelope
└──────────────────────────┘
            │ MCP tool registration
            ▼
   CC sees: memory.palace_get, channel.read, ...
```

### 6.2 Why IMAP, not MCP-as-transport

| Option | Verdict |
|---|---|
| **IMAP envelopes (chosen)** | Already shipped infrastructure. Self-healing via `BusLauncher`. Persistent, durable, supports IDLE for push. Same bus everything else uses — no new wire protocol. Surface adapters translate at each end. |
| MCP as transport | MCP is a *consumer* surface, not a transport. Putting announce-MCP at the wire level forces every agent to speak MCP, which is wrong for Igor (Igor's a Python program; tool calls are direct method calls). MCP-as-surface for CC is correct because CC IS an MCP host. |
| HTTP | Reasonable third option. Would need a new server. The bus already exists, so default to bus. HTTP becomes a *fourth* surface adapter (web dashboard reads manifests from the announce broker over HTTP — Phase 2). |
| Direct Python import | Works only for in-process agents. Igor crosses processes. Doesn't generalize. |

### 6.3 Wire shapes

**Announce request** (Igor or CC sending):

```python
# agent-side
env = Envelope.now(
    from_device="igor.wild-0001@akiendelllinux.1",
    to_device="announce",
    payload={
        "intent": "announce.request",
        "identity": identity_envelope.to_dict(),
        "request_id": "req-uuid4",
    },
)
router.send("comms://announce", env)
# Then poll/IDLE on comms://igor for the reply with payload.intent == "announce.manifest"
```

**Announce response** (broker sending):

```python
# broker-side
manifest = ManifestAssembler(profile_store, registry, imap).assemble(identity)
env = Envelope.now(
    from_device="announce",
    to_device=identity.primary_mailbox(),  # comms://akiendelllinux.1
    payload={
        "intent": "announce.manifest",
        "manifest": manifest.to_dict(),
        "request_id": original_request_id,  # so agent can correlate
    },
)
router.send(f"comms://{identity.primary_mailbox()}", env)
```

The agent-side wait can be either:
- **Synchronous wait with timeout** — agent blocks reading its own inbox via IMAP IDLE until manifest arrives, max 5s. (v1 default.)
- **Async / poll** — agent sends, returns immediately, manifest arrives later and gets stashed. (Phase 2.)

---

## 7. Dynamic re-announce — push-on-change with idempotent pull

### 7.1 When the manifest changes

| Trigger | Source | Push? |
|---|---|---|
| New device registers | `Skeleton.register_device` `skeleton.py:90` | Push to all agents whose profile matches the new device |
| Device deregisters / goes offline | `Skeleton.deregister_device` `skeleton.py:137` | Push to all agents that had it in their manifest |
| Profile YAML edited on disk | `inotify` watch on `~/.agent_datacenter/profiles/` | Push to agents of the changed type only |
| ACL change | (future) ACL admin tool | Push to affected agents |
| Registry file edited externally | `inotify` on `~/.agent_datacenter/devices.json` | Push to all agents (registry_etag changes) |

### 7.2 Push mechanism: announce-events channel

The skeleton creates a built-in channel `comms://announce-events`. Every
agent that has plugged in is a member of this channel. On any change above,
the announce broker:

1. Determines the affected agents (set of agent_ids matching the change).
2. Posts an event to `comms://announce-events` with payload:
   ```json
   {
     "intent": "announce.invalidate",
     "affected": ["igor", "cc"],   // or ["*"] for all
     "reason": "device.online: discord_bot",
     "manifest_etag_hint": "sha256:..."
   }
   ```
3. Each affected agent's adapter, on receiving the invalidation, sends a
   fresh `announce.request` and replaces its in-memory manifest.

### 7.3 Idempotence

Three keys:

1. **`manifest_id` is a uuid4 per assembly.** Agents store the most recent
   `manifest_id`. If they receive a duplicate (e.g. from a retry), they
   no-op.
2. **`profile_etag` and `registry_etag` are SHA-256 over the inputs.** Agents
   can ask "do I need to re-fetch?" by sending an envelope with
   `intent: announce.check`, payload `{"current_etags": {...}}`. Broker
   replies with `announce.unchanged` if etags match, else with the full
   manifest. This is the cheap-pull path.
3. **Tool bindings are addressed by name.** Re-announce that produces the
   same tool with the same address is a no-op for the consumer; tool that
   disappears is unregistered; new tool is registered.

### 7.4 Agent's expected response to an invalidation

```python
# datacenter_client.py (Igor side, sketch)
def on_announce_invalidate(event: dict) -> None:
    affected = event.get("affected", [])
    if "*" not in affected and self.agent_id not in affected:
        return  # not for us; ignore
    log.info("announce invalidate: %s", event.get("reason"))
    new_manifest = self.fetch_manifest()
    self.swap_manifest(new_manifest)  # atomic; rebuilds system prompt next call
```

CC-side equivalent: re-register the MCP tools with the new manifest's tool
list. Whether MCP supports dynamic tool registration mid-session is an
open question (§ 11.D) — fallback is "next-session-only" with a warning
nudge to Akien via YGM that an MCP refresh is recommended.

---

## 8. Composition with existing primitives

### 8.A Existing `comms://igor-wild-0001` URL-style (lineage form)

**Decision: alias, don't replace.** v1.

- **Primary routing form:** `comms://<box>.<n>` (e.g., `comms://akiendelllinux.1`).
- **Lineage alias:** `comms://igor-wild-0001` resolves through a soft-alias
  table maintained by the announce broker:
  ```python
  # ~/.agent_datacenter/aliases.json — atomic-write, mirrors registry
  {
    "igor-wild-0001": "akiendelllinux.1",
    "cc.0":          "akiendelllinux.1.cc.0"
  }
  ```
- The router's `resolve()` consults `aliases.json` after the primary
  mailbox lookup fails. This is a small, additive router change at
  `router.py:60-81`.
- Why alias not replace: there are existing test fixtures and seed scripts
  that use the lineage form. A flag day breaks them; aliasing is
  zero-cost.
- **Open question (§ 11.E):** when to flip the alias to "deprecated, will
  be removed" — sprint scope or later.

### 8.B `cc_queue.py` palace canonical store + `queue.json` echo

**Orthogonal — leave alone.** The announce protocol doesn't touch the
ticket queue. Tickets are state; capabilities are bindings. The only
intersection: the announce manifest *might* one day bind a `tickets.next()`
tool that wraps `cc_queue.py` for the worker daemon, but that's a separate
device-extraction ticket, not part of announce.

### 8.C `lab/claudecode/channel.py`

**Already on the deprecation path** — see channel.py:1-9 header. The
announce protocol delivers the `comms://shared` address as a manifest
subscription, so:

- The CC-side announce-MCP adapter exposes `channel_read` and
  `channel_post` MCP tools that route to `comms://shared` directly.
- `channel.py` becomes a thin compatibility CLI wrapper that wraps those
  same MCP tools (or routes directly via the bus) — JSONL fallback gets
  removed when the IMAP-only path is verified e2e.
- **Migration:** file a child ticket `T-channel-py-thin-shim-over-announce`
  scoped after announce ships.

---

## 9. Igor-side consumer

### 9.1 New file: `wild_igor/igor/datacenter_client.py`

```python
"""
DatacenterClient — Igor's bridge to the announce broker.

Loads at boot, sends an IdentityEnvelope, receives a Manifest, exposes
typed accessors used by system_prompt.py + turn_pipeline.py +
reasoning_workflow.py.

Subscribes to comms://announce-events for push-on-change.
"""
from __future__ import annotations
import json, os, socket, uuid, threading, logging
from dataclasses import asdict
from datetime import datetime, timezone

from bus.envelope import Envelope
from bus.imap_server import IMAPServer
from agent_datacenter.bus.router import Router

log = logging.getLogger(__name__)

class DatacenterClient:
    def __init__(self, instance_id: str = "wild-0001"):
        self.agent_id = "igor"
        self.instance_id = instance_id
        self.box = socket.gethostname().split(".")[0]
        self.box_n = int(os.environ.get("IGOR_BOX_N", "1"))
        self._imap = IMAPServer()  # connects to running rack
        self._router = Router(self._imap)
        self._manifest: dict | None = None
        self._lock = threading.Lock()
        self._invalidate_thread: threading.Thread | None = None

    def primary_mailbox(self) -> str:
        return f"{self.box}.{self.box_n}"

    def boot(self) -> dict:
        """First-boot: send identity envelope, wait for manifest, start invalidate listener."""
        identity = self._build_identity()
        self._imap.create_mailbox(self.primary_mailbox())   # ensure inbox exists
        self._send_announce_request(identity)
        manifest = self._wait_for_manifest(timeout_s=5)
        if manifest is None:
            raise RuntimeError("DatacenterClient: announce timed out")
        with self._lock:
            self._manifest = manifest
        self._start_invalidate_listener()
        return manifest

    def manifest(self) -> dict:
        with self._lock:
            if self._manifest is None:
                raise RuntimeError("DatacenterClient: not booted")
            return self._manifest

    def tool_address(self, tool_name: str) -> str:
        for t in self.manifest()["tools"]:
            if t["name"] == tool_name:
                return t["address"]
        raise KeyError(f"tool {tool_name!r} not in manifest")

    def state_ref(self, name: str) -> dict | None:
        for s in self.manifest()["state_refs"]:
            if s["name"] == name:
                return s
        return None

    def channels(self) -> list[dict]:
        return list(self.manifest()["subscriptions"])

    # ── Internals ────────────────────────────────────────────────────────
    def _build_identity(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "instance": self.instance_id,
            "box": self.box,
            "box_n": self.box_n,
            "pid": os.getpid(),
            "interface_version": "1.0",
            "announce_schema": "1.0",
            "lineage": f"Igor-{self.instance_id}",
            "coa_id": os.environ.get("IGOR_COA", "primary"),
            "surfaces": ["console", "inference"],
            "declared_capabilities": ["cognition"],
            "proof": {"uid": os.getuid()},
        }

    def _send_announce_request(self, identity: dict) -> None:
        env = Envelope.now(
            from_device=self.primary_mailbox(),
            to_device="announce",
            payload={
                "intent": "announce.request",
                "identity": identity,
                "request_id": str(uuid.uuid4()),
            },
        )
        self._router.send("comms://announce", env)

    def _wait_for_manifest(self, timeout_s: float = 5.0) -> dict | None:
        # IMAP IDLE on primary mailbox until envelope with intent=announce.manifest
        # ... implementation detail; exits early on first match or returns None on timeout
        ...

    def _start_invalidate_listener(self) -> None:
        def loop():
            for env in self._imap.idle("announce-events"):
                payload = env.payload
                if payload.get("intent") != "announce.invalidate":
                    continue
                affected = payload.get("affected", [])
                if "*" not in affected and self.agent_id not in affected:
                    continue
                log.info("manifest invalidated: %s", payload.get("reason"))
                identity = self._build_identity()
                self._send_announce_request(identity)
                new_m = self._wait_for_manifest(5)
                if new_m:
                    with self._lock:
                        self._manifest = new_m
                    # Notify system_prompt cache to invalidate
                    from .cognition.system_prompt import invalidate_cache
                    invalidate_cache()
        t = threading.Thread(target=loop, name="announce-invalidate-listener", daemon=True)
        t.start()
        self._invalidate_thread = t
```

### 9.2 Integration with `system_prompt.py`

Current `system_prompt.py` (lines 40-269) builds the prompt from cortex
memories only. The integration adds a new layer between LAYER 1c and
LAYER 2, sourced from the manifest:

```python
# Inserted ~line 224 in system_prompt.py
def build_system_prompt(cortex, instance_id="wild-0001", role="interactive",
                       dc_client: "DatacenterClient | None" = None):
    ...
    if dc_client is not None and role == "interactive":
        manifest = dc_client.manifest()
        lines.extend(_render_capability_layer(manifest))
    ...

def _render_capability_layer(manifest: dict) -> list[str]:
    """LAYER 1d: capability binding — what Igor can reach right now."""
    lines = ["", "BOUND CAPABILITIES (from datacenter manifest):"]
    for tool in manifest["tools"]:
        lines.append(f"  - {tool['name']} ({tool['permission_mode']}) "
                     f"→ {tool['address']}")
        if tool.get("description"):
            lines.append(f"      {tool['description']}")
    if manifest["subscriptions"]:
        lines.append("")
        lines.append("CHANNELS (you are a member; messages here may need response):")
        for sub in manifest["subscriptions"]:
            lines.append(f"  - {sub['name']} ({sub['address']})")
    if manifest["state_refs"]:
        lines.append("")
        lines.append("STATE REFERENCES (your cognition lives here):")
        for s in manifest["state_refs"]:
            lines.append(f"  - {s['name']:8} → {s['uri']}  [{s['mode']}]")
    return lines
```

The prompt cache key (currently SHA-256 of narratives + role + instance,
`system_prompt.py:73-78`) extends to include `manifest['profile_etag'] +
manifest['registry_etag']` — when the manifest changes, the cache misses
and the prompt rebuilds.

`invalidate_cache()` (line 385) is already the right hook —
`DatacenterClient._start_invalidate_listener` calls it on every
invalidation. The wiring is one line added in the existing function.

### 9.3 Integration with `turn_pipeline.py` and `reasoning_workflow.py`

`turn_pipeline.py` (read at lines 1-100) describes the cascade →
workflow → decision-blob → voice flow. The DatacenterClient is injected
into `IgorBase` (`turn_pipeline.py:67` already imports IgorBase) so that:

- `experiment_cascade` and `reasoning_workflow` query
  `dc_client.tool_address("inference.complete")` instead of hardcoding
  the inference path.
- The peer advisor (`reasoning_workflow.py:PeerAdvisor`) routes through
  whichever address the manifest binds — Igor on another box, an Ollama
  endpoint, an OR proxy, all interchangeable.
- Tool dispatch (`<tool>name</tool>` per `system_prompt.py:184`) checks
  the manifest for the requested tool name and bus-routes accordingly.

Concrete integration point: `IgorBase.__init__` gains a `dc_client`
attribute, populated in main.py during boot. Existing direct imports of
inference, browser_use, etc. become bus-routed via the manifest's
`tool_address()` lookup.

### 9.4 Boot sequence (revised)

```
main.py (igor entry):
  1. boot logger
  2. DatacenterClient(instance_id).boot()         # NEW — sends identity, gets manifest
  3. cortex = Cortex(...)                         # state_refs from manifest tell us where
  4. system_prompt = build_system_prompt(cortex, dc_client=client)
  5. turn_pipeline = TurnPipeline(igor_base=IgorBase(cortex, dc_client))
  6. main loop ...
```

If step 2 fails (no rack running), fall back to `_fallback_prompt` and
log a WARNING — Igor stays usable degraded.

---

## 10. CC-side consumer

### 10.1 Verifying the intuition: yes, an MCP server in `agent_datacenter/devices/claude/`

**Confirmed.** The right pattern is:

- **New device:** `agent_datacenter/devices/claude/announce_mcp.py` — an
  MCP server (using `fastmcp`, same lib the skeleton uses,
  `skeleton.py:24`) that runs as a stdio MCP process spawned by Claude
  Code's MCP config.
- **On boot,** the server:
  1. Reads `CLAUDE_SESSION_ID` env var (set by Claude Code).
  2. Builds an `IdentityEnvelope` (`agent_id="cc"`, `instance="session-<id>"`).
  3. Connects to the local IMAP rack.
  4. Sends `announce.request` to `comms://announce`.
  5. Receives the manifest.
  6. **Dynamically registers** each tool in the manifest as an MCP tool
     via `@mcp.tool()`, with the input/output schemas from the manifest
     and a thin handler that wraps the `comms://` address into a routed
     envelope.
  7. Subscribes to `comms://announce-events` and re-registers tools on
     invalidation (with the caveat in § 7.4).
- **MCP config:** `~/TheIgors/.mcp.json` (already exists; current shape
  inspected) gets a new entry:
  ```json
  {
    "mcpServers": {
      "datacenter": {
        "command": "/home/akien/dev/src/agent_datacenter/.venv/bin/python",
        "args": ["-m", "devices.claude.announce_mcp"],
        "env": {
          "CLAUDE_SESSION_ID": "${CLAUDE_SESSION_ID}",
          "AGENT_DATACENTER_HOME": "${HOME}/.agent_datacenter"
        }
      },
      "igor": { "...": "..." }
    }
  }
  ```
  The existing `igor` entries stay until announce is verified end-to-end;
  then they fold into the datacenter announce (`request_compaction`
  becomes a manifest tool).

### 10.2 Concrete sketch

```python
# agent_datacenter/devices/claude/announce_mcp.py
"""
AnnounceMCP — CC-side MCP adapter for the datacenter announce protocol.

Spawned by Claude Code's mcp.json. Translates manifest tools into
@mcp.tool decorated callables. Each call routes a comms:// envelope and
waits for a reply.
"""
from __future__ import annotations
import os, uuid, json, socket
from mcp.server.fastmcp import FastMCP
from bus.envelope import Envelope
from bus.imap_server import IMAPServer
from agent_datacenter.bus.router import Router

mcp = FastMCP("datacenter-announce")
_imap = IMAPServer()
_router = Router(_imap)
_session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
_box = socket.gethostname().split(".")[0]
_my_mailbox = f"{_box}.1.cc.{_session_id}"

def _identity():
    return {
        "agent_id": "cc",
        "instance": f"session-{_session_id}",
        "box": _box,
        "box_n": 1,
        "pid": os.getpid(),
        "interface_version": "1.0",
        "announce_schema": "1.0",
        "surfaces": ["mcp", "console"],
        "declared_capabilities": ["editor", "shell"],
        "proof": {"uid": os.getuid()},
    }

def _fetch_manifest() -> dict:
    _imap.create_mailbox(_my_mailbox)
    env = Envelope.now(
        from_device=_my_mailbox,
        to_device="announce",
        payload={"intent": "announce.request", "identity": _identity(),
                 "request_id": str(uuid.uuid4())},
    )
    _router.send("comms://announce", env)
    # IMAP IDLE on _my_mailbox; return manifest payload
    ...

def _register_tools(manifest: dict) -> None:
    """Each tool in the manifest becomes an @mcp.tool callable."""
    for tool in manifest["tools"]:
        _make_tool(tool)

def _make_tool(tool: dict) -> None:
    name = tool["name"].replace(".", "_")  # MCP names are flat
    address = tool["address"]
    @mcp.tool(name=name, description=tool.get("description", ""))
    def _call(**kwargs) -> dict:
        env = Envelope.now(
            from_device=_my_mailbox,
            to_device=address.replace("comms://", ""),
            payload={"intent": tool["name"], "args": kwargs,
                     "request_id": str(uuid.uuid4())},
        )
        _router.send(address, env)
        # IMAP IDLE on _my_mailbox; await reply matching request_id
        ...
    return _call

if __name__ == "__main__":
    manifest = _fetch_manifest()
    _register_tools(manifest)
    # invalidate listener loop spawned in background thread
    mcp.run()
```

### 10.3 Boot-time handshake

1. Claude Code launches the `datacenter` MCP server (per `mcp.json`).
2. Server connects to local IMAP, sends `announce.request`.
3. Server blocks (with timeout) waiting for `announce.manifest`.
4. Server registers each tool as an MCP tool, then enters `mcp.run()`.
5. Claude Code receives the tool list at MCP handshake time.
6. From Akien's POV in CC: `memory_palace_get`, `channel_read`,
   `channel_post`, `browser_use_fetch`, `swadl_run_skill` are all
   listed by the MCP host as available — sourced from the announce
   manifest, not from a static config file.

The existing `ygm_check` hook (`devices/claude/shim.py:34-37` and the
hook entry in `~/.claude/settings.json`) is unchanged; it's a separate
nudge-pipeline path that sits alongside announce.

---

## 11. Open questions for human decision

Liberal flagging — first-pass design, not final spec.

### A. Surface addressing form

Path-style (`comms://cc.0/console`) vs suffix-style
(`comms://cc.0.console`)?

- The existing router supports only flat mailbox names (§ 2). Suffix-style
  is the zero-router-change choice and matches how `CC.0` / `CC.<session>`
  already work.
- Path-style reads more like a URL and matches the design-doc text
  verbatim.
- **Recommendation:** suffix. **Question for Akien:** is the URL aesthetic
  load-bearing in the design doc, or paraphrasable?

### B. Multi-COA identity granularity

`<box>.<n>` alone isn't enough for cognition-bearing agents that may host
multiple COAs (per `T-concurrent-ne-spawn` + design doc § "Multi-COA"
lines 113-126).

- Option 1: `<box>.<n>.<coa_id>` as primary mailbox (one mailbox per COA).
- Option 2: `<box>.<n>` is one mailbox; envelopes carry `coa_id` in
  payload; agent dispatches internally.
- **Recommendation:** Option 1 — addressing-level separation matches the
  "channel between two COAs doesn't care if same process or different
  boxes" framing in the design doc (line 121). Mailbox per COA gives
  cross-box uniformity for free.
- **Question for Akien:** confirmed?

### C. Profile inheritance

The schema accepts `inherits: [...]` but v1 ships with the merge function
as TODO. Should v1 actually implement merge, or defer?

- v1 with no inheritance: every profile is hand-edited, duplication
  expected.
- v1 with inheritance: research-orca cleanly inherits cc-base.
- **Recommendation:** ship inheritance in v1 with a well-defined merge
  rule (deep-merge, child wins on key collision; lists concatenate
  unless overridden by a `__replace__` marker). Cost is ~30 lines of
  Python; ROI is large because future profiles will lean on it.
- **Question for Akien:** ship inheritance v1 or v2?

### D. MCP dynamic tool re-registration on invalidate

Does the MCP SDK support live tool list mutation during a session, or is
tool list frozen at handshake?

- If frozen: the announce-MCP server must restart to refresh. UX cost:
  Akien sees tools disappear briefly. Mitigation: announce-MCP shim
  catches invalidate, restarts itself (Claude Code MCP config typically
  auto-restarts crashed servers).
- If supported: live add/remove via FastMCP API.
- **Action item for sprint:** read FastMCP docs / source to confirm.
  Listed here because the answer changes the v1 reconnect behavior.

### E. Lineage alias deprecation timeline

`comms://igor-wild-0001` aliased to `comms://akiendelllinux.1` — when do
we mark deprecated, when do we remove?

- Lots of seed scripts (`lab/claudecode/seed_*.py`) reference the lineage
  form. Removal touches many files.
- **Recommendation:** mark deprecated v1, sweep in a child ticket
  `T-comms-lineage-alias-removal` after announce ships and is verified.
- **Question for Akien:** acceptable?

### F. Permission model: announce-time filter only, or runtime ACL?

The manifest filters at announce time (e.g., CC's profile says
`postgres: read_only` so the manifest only binds read tools). But the
announce-MCP server is a process Akien (the user) controls — nothing
prevents him from manually bypassing.

- Option A: announce-time filter only (current design). Simple. Adequate
  for v1's localhost trust model.
- Option B: every envelope carries `from_device`; receiving devices
  re-check ACL on dispatch. Defense-in-depth.
- **Recommendation:** A for v1, B for Phase 5+ (cross-box, multi-user).
- **Question for Akien:** confirmed?

### G. Bootstrap minimum — what does an agent need to know to plug in?

The design assumes the agent knows the announce mailbox address
(`comms://announce`) and the IMAP server location. These have to come
from somewhere outside the manifest (chicken-and-egg).

- Option A: hardcoded constants in `agent_datacenter` package — every
  agent imports.
- Option B: env vars `AGENT_DATACENTER_ANNOUNCE` /
  `AGENT_DATACENTER_IMAP_URL` set by the rack on launch.
- Option C: `~/.agent_datacenter/bootstrap.json` — small flat file the
  rack writes; agents read.
- **Recommendation:** C, mirroring the registry pattern — atomic file,
  no DB dependency, machine-readable.
- **Question for Akien:** confirmed?

### H. Re-announce push channel — IMAP IDLE or polling?

The design uses a dedicated `comms://announce-events` channel + IMAP
IDLE for low-latency push.

- IMAP IDLE has session limits (RFC 2177: ~29 minutes between heartbeats).
  Long-lived agents need re-IDLE logic.
- Polling is simpler but adds latency.
- **Recommendation:** IDLE with 25-minute heartbeat refresh, polling
  fallback every 60s if IDLE drops.
- **Question for Akien:** confirmed, or simpler to start polling-only?

### I. Manifest persistence on agent side

Should agents persist the last manifest to disk (e.g.,
`~/.TheIgors/igor_wild_0001/manifest.json`) so they can boot
degraded if the rack is briefly down?

- Pro: crash resilience; Igor doesn't lose orientation if rack
  restarts.
- Con: stale manifest can mis-bind tools; Igor speaks to ghosts.
- **Recommendation:** persist with a `stale_after_s` advisory field
  (~5 min); on boot if stale, log WARNING and degrade to fallback.
- **Question for Akien:** confirmed?

### J. Profile location: `agent_datacenter/config/profiles/` (in repo) or `~/.agent_datacenter/profiles/` (runtime)?

- Repo path: profiles versioned in git, edited via PR.
- Runtime path: editable on the box, no PR friction.
- **Recommendation:** both, with sync-on-install. Repo is canonical;
  runtime is the read path (matches `device_config.py`'s
  `agent_datacenter_home()` pattern).
- **Question for Akien:** confirmed?

### K. CC's palace permission level — `read_write` (current default) or tighten to `read_only`?

The proposed CC profile sets `postgres: read_write` because that
matches CC's current behavior — `cc_queue.py` writes to `clan.memories`
(`parent_id='TICKETS_ROOT'`), `/decided` writes decision rollups to the
palace, slate updates write `theigors/slates/*`, `/note` writes notes
log, `palace_sync.py` keeps `lab/theigors/` echo aligned.

A previous draft of this doc set CC to `read_only` with the comment
"CC reads the palace, Igor writes it" — that's aspirational, not
current. Imposing `read_only` at announce-time would silently break
~10+ CC workflows the moment the manifest becomes the source of truth.

- Option A (current draft): `read_write`. Matches reality. No surprise
  breaks.
- Option B: `read_only`. Cleaner separation. Requires migrating
  ticket / slate / decision write paths to Igor or to a new
  workshop-side device first. A migration ticket
  (e.g. `T-cc-palace-write-paths-to-workshop-device`) becomes a hard
  prerequisite of announce going live.
- **Recommendation:** Option A v1. File Option B as a future direction
  after the workshop-device split is mature.
- **Question for Akien:** confirmed, or is the cleaner separation worth
  the migration cost?

---

## 12. Test plan (per ticket, condensed here)

### 12.A `tests/test_announce_protocol.py` (agent_datacenter side)

- `test_identity_envelope_validates` — happy path + missing required
  field raises.
- `test_profile_resolution_reads_yaml` — writes a fixture profile,
  `load_profile` returns expected shape.
- `test_profile_inherits` — when shipping inheritance (§ 11.C).
- `test_manifest_assembly_filters_by_profile` — Igor profile binds
  inference; CC profile does not bind cognition state_refs.
- `test_manifest_assembly_excludes_offline_devices` — deregister a
  device, manifest no longer lists it.
- `test_invalidate_on_device_register` — register a new matching
  device, agent receives invalidate event.
- `test_invalidate_on_profile_edit` — touch profile YAML, inotify
  fires, agent receives invalidate event.
- `test_etag_unchanged_returns_announce_unchanged` — agent sends
  `announce.check` with current etags, broker replies short-circuit.

### 12.B `tests/test_igor_datacenter_client.py` (TheIgors side)

- `test_boot_sends_identity` — boot fires an envelope to
  `comms://announce`.
- `test_boot_blocks_until_manifest_or_timeout` — synthetic broker
  replies, client returns; broker silent → client raises after 5s.
- `test_system_prompt_layer_includes_capabilities` — passes a stub
  manifest; built prompt contains tool names + state_refs.
- `test_invalidate_rebuilds_prompt_cache` — fire invalidate; cache key
  changes; next prompt build pulls fresh.
- `test_tool_address_lookup_for_inference` — `dc_client.tool_address("inference.complete")`
  matches manifest.

### 12.C CC-side smoke test

- `tests/test_announce_mcp_smoke.py` — spawn the announce-MCP server
  with a mock broker; assert `mcp.list_tools()` returns the manifest's
  tool names.
- Assert the MCP `request_compaction` tool resolves through this path
  (regression guard against current `igor_mcp.py` direct dependency).

---

## 13. File-create / file-touch summary (for sprint)

**New files:**

- `agent_datacenter/agent_datacenter/announce/__init__.py`
- `agent_datacenter/agent_datacenter/announce/envelope.py` — IdentityEnvelope dataclass
- `agent_datacenter/agent_datacenter/announce/manifest.py` — Manifest + ToolBinding + ChannelSubscription + StateRef + ACL dataclasses
- `agent_datacenter/agent_datacenter/announce/profile.py` — load_profile, merge for inheritance
- `agent_datacenter/agent_datacenter/announce/broker.py` — AnnounceBroker (subdevice of skeleton); ManifestAssembler
- `agent_datacenter/agent_datacenter/announce/invalidator.py` — inotify watch + push-on-change
- `agent_datacenter/config/profiles/igor.yaml`
- `agent_datacenter/config/profiles/cc.yaml`
- `agent_datacenter/config/profiles/research-orca.yaml` (example)
- `agent_datacenter/devices/claude/announce_mcp.py` — CC-side MCP adapter
- `wild_igor/igor/datacenter_client.py` — Igor-side consumer
- `~/.agent_datacenter/bootstrap.json` — written by rack at boot, read by all agents
- `~/.agent_datacenter/aliases.json` — lineage alias table

**Touched files:**

- `agent_datacenter/agent_datacenter/skeleton/skeleton.py` — register AnnounceBroker as a sub-device; add `rack.announce_request` MCP tool for debugging
- `agent_datacenter/agent_datacenter/bus/router.py` — alias-table consult after primary lookup
- `agent_datacenter/bus/imap_server.py` — ensure mailbox `announce` and `announce-events` exist at boot
- `wild_igor/igor/cognition/system_prompt.py` — accept `dc_client`, render capability layer; cache key includes manifest etags
- `wild_igor/igor/cognition/turn_pipeline.py` — IgorBase gains `dc_client`; tool dispatch consults manifest
- `wild_igor/igor/cognition/reasoning_workflow.py` — peer advisor address sourced from manifest
- `wild_igor/igor/main.py` — boot DatacenterClient before cortex
- `lab/claudecode/channel.py` — header note: superseded by manifest-bound channel tools
- `~/TheIgors/.mcp.json` — new `datacenter` server entry (existing `igor` entries remain transitional)

---

## 14. Headline decisions (for the cover summary)

1. **Profile (static, YAML, runtime dir) and Manifest (dynamic, derived,
   per-announce) are sharply distinct.** Profile lives in
   `~/.agent_datacenter/profiles/<agent_id>.yaml` (committed under
   `agent_datacenter/config/profiles/`, synced on install). Manifest is
   computed by an `AnnounceBroker` subdevice of the skeleton on every
   announce request.

2. **Single transport: IMAP envelopes on the existing bus.** Surface
   adapters at each end (`datacenter_client.py` for Igor;
   `announce_mcp.py` for CC) translate to native idioms. MCP and HTTP
   are *consumer* surfaces, not transports.

3. **Surface addresses are mailbox suffixes**
   (`comms://akiendelllinux.1.console`), not URL paths
   (`comms://akiendelllinux.1/console`). Reason: the router treats
   `comms://X` as a flat mailbox lookup; suffix-style is zero
   router-change. (Open question § 11.A — Akien may prefer path-style.)

4. **Lineage form (`comms://igor-wild-0001`) is aliased, not replaced,
   in v1.** Alias table at `~/.agent_datacenter/aliases.json`.
   Deprecation sweep is a child ticket.

5. **Re-announce is push-on-change via a built-in
   `comms://announce-events` channel.** Idempotence via `manifest_id`
   and etags. Agents respond by re-fetching and atomic-swapping their
   in-memory manifest.

6. **Igor's system prompt gains a "BOUND CAPABILITIES" layer** sourced
   from the manifest, with the prompt cache key extended by the
   manifest's `profile_etag + registry_etag` so cache invalidates
   correctly.

7. **CC plugs in via a new MCP server**
   (`agent_datacenter/devices/claude/announce_mcp.py`) registered in
   `~/TheIgors/.mcp.json`. Each manifest tool becomes a dynamically
   registered MCP tool. The existing `igor` MCP entries stay during
   transition.

8. **Trust model is unchanged from existing rack: localhost-uid trust.**
   No HMAC, no token. Cryptographic ACL deferred to Phase 5+.

9. **`channel.py` becomes a thin shim over manifest-bound channel
   tools** — it's already on the deprecation path (file header lines
   1-9). Sweep is a child ticket.

10. **`cc_queue.py` is orthogonal** — tickets are state, capabilities
    are bindings. No interaction with announce.

---

## 15. Top open questions Akien must decide before sprint

(See § 11 for full list. The ones that gate the design most are:)

1. **§ 11.A — Surface addressing form** (path vs suffix). Recommends
   suffix; defers to Akien.
2. **§ 11.B — Multi-COA mailbox granularity** (`<box>.<n>` vs
   `<box>.<n>.<coa>`). Recommends per-COA mailbox.
3. **§ 11.C — Ship profile inheritance in v1?** Recommends yes (~30
   lines, big ROI).
4. **§ 11.D — MCP dynamic tool re-registration**. Action item: confirm
   FastMCP capability before sprint.
5. **§ 11.G — Bootstrap minimum** for agents to plug in
   (`bootstrap.json` recommended).

Smaller open items (§§ 11.E, F, H, I, J, K) can be ratified at sprint
with the recommendations as defaults.

---

## 14. Akien decisions on § 11 open questions (2026-05-01 review)

All 11 questions reviewed and resolved during the same-day Opus-pass review session.

| § | Decision | Notes |
|---|---|---|
| 11.A — addressing form | **Suffix** (`comms://cc.0.console`) | Opus rec accepted. URL aesthetic in design doc is paraphrasable. |
| 11.B — multi-COA mailbox granularity | **Per-COA** (`<box>.<n>.<coa>`) | Opus rec accepted. |
| 11.C — profile inheritance v1 or v2 | **v1** | Opus rec accepted. Ship deep-merge with `__replace__` marker. ~30 lines, large ROI. |
| 11.D — MCP dynamic tool re-registration | **Action item, not a question** | Sprint-time check FastMCP support before implementing reconnect-on-invalidate. |
| 11.E — lineage alias deprecation timeline | **Deprecate on ship, not later** | More aggressive than Opus rec ("deprecate v1, sweep child ticket later"). Akien framing: research project, single user, "if it breaks we fix it." File `T-comms-lineage-alias-removal` as a same-cycle ticket, not deferred. |
| 11.F — permission model | **Announce-time filter only (v1)** | Opus rec accepted. Runtime ACL re-check is Phase 5+ (cross-box, multi-user). |
| 11.G — bootstrap minimum | **In the shim, not a separate `bootstrap.json`** | Refines Opus rec. Each agent has a shim. Igor needs one. The shim carries: install instructions, connection logic, capability-reading. The shim IS the durable bootstrap surface — not a file the rack writes. Connects directly to the install-flow vision in T-claudeandakien-workshop-evolution. |
| 11.H — re-announce push: IDLE or polling | **Reframed: read-and-remove pattern; session limits become near-irrelevant** | Akien's reframe: each shim continuously **reads AND removes** messages from its inbox. The IMAP becomes pure delivery transport (deliver-and-go), not a long-lived state store. Persistence lives elsewhere (per-agent log + palace). The web window's already-scrolled rendered DOM is the user-visible history; removing from IMAP doesn't affect it. With short-lived consume-and-delete, IDLE 29-min session limits matter much less. Sprint-time question Akien asked: can we remove the session limits entirely on our side? (We control the IMAP server — Dovecot config, or our Python stub — so likely yes.) |
| 11.I — manifest persistence on agent side | **Persist with `stale_after_s` ~5 min** | Opus rec accepted. On boot, if stale, log WARNING and degrade to fallback. |
| 11.J — profile location | **Both — repo canonical, runtime read** | Opus rec accepted. Sync-on-install. Matches existing `agent_datacenter_home()` pattern. |
| 11.K — CC palace permissions | **read_write** | Opus rec accepted. Reason Akien gave: "you're his doctor — you need to be able to mod anything." Cleaner separation deferred to post-workshop-device split. |

**Cross-cutting reminder Akien flagged:** the SQLite-removal work has 3 outstanding open tickets and 3 actively-written `.db` files (`wild-0001.db`, `word_graph.db`, `claude_budget.db`). Postgres-only is the rule; this is a real ongoing migration debt. Reorg-Opus (companion pass) flagged the live `.db` files for Akien-decided cleanup.

**Implications for the next sprint:**
- E-decision changes the deprecation cadence: file the lineage-alias-removal ticket as part of v1, not deferred.
- G-decision shifts how bootstrap is implemented: Igor needs a shim added to `agent_datacenter/devices/igor/shim.py` (likely already partially exists — verify) that carries the install + connect + capability-reading methods.
- H-reframe simplifies IMAP usage: shims drain inbox; web reads from a separate event log (per-agent or palace-channel).

---

*Drafted 2026-05-01 by Claude Code Opus 4.7 (opus-pass) per
T-datacenter-capability-announce-protocol. § 14 added by Claude Haiku 4.5
during same-day Akien review. Foundational; gates the wider
T-capability-extraction-from-igor work.*
