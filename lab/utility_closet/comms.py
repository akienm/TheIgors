"""comms.py — Channel routing, message envelopes, and transport dispatch.

WHAT IT IS
──────────
Lt Uhura's console: all routing, no participation. Comms is the unified
messaging layer for the whole system. Every message between agents (Igor,
CC, web UI, external systems) flows through a standard envelope and gets
routed to pluggable transports. Channels are identified by comms:// URIs;
messages inherit retention and logging behavior from channel config.

WHY IT EXISTS
─────────────
Igor's cognition is distributed — memory graph, inference requests, skill
invocations, habit dispatch all generate inter-process messages. Without
a unified comms layer (D335), messaging would scatter across
subprocess.Popen, raw TCP, files, and direct LLM calls. Comms centralizes:
single envelope, single subscriber model, single file-logging surface.
This makes the system debuggable, enables multi-instance comms on shared
Postgres, and makes CC ↔ Igor conversation first-class infrastructure
rather than ad-hoc relaying.

HOW IT WORKS (architecture)
───────────────────────────
Three collaborating layers:

1. comms.py (this file) — envelope + channel registry. Exposes send(),
   read(), subscribe(). Routes to transports via channel address. All
   retention/logging behavior derived from Channel config.

2. Transport base (Transport class) — pluggable send/read backends.
   Implementations live in lab/utility_closet/transports/:
     postgres.py  — persistent history in infra.channel_messages (D210)
     discord.py   — bridges to discord_bot module
     inference.py — LLM calls as comms messages (request/response)
     or_chat.py   — stateful chat: scrollback-aware multi-turn
     memory.py    — in-memory deque (testing, ephemeral channels)
   Each transport implements send(channel, message) → bool and
   read(channel, limit, since) → list[ChannelMessage].

3. Utility closet web server — HTTP/WebSocket front-end.
   lab/claudecode/utility_closet_server.py wraps CommsModule. /api/cc_send
   routes POST → channel.send(). WebSocket subscribers get broadcast on
   every message. channel_messages table (infra schema) is the persistent
   log.

ChannelMessage envelope
───────────────────────
  id           — uuid hex (16 chars), set by envelope
  channel      — comms:// URI
  source       — actor id (igor-wild-0001, ccmain, akien, inference-gateway)
  timestamp    — ISO8601, set at send() time
  content_type — MIME type (text/plain, text/markdown, inference/request)
  payload      — message body
  reply_to     — optional correlation ID for req/resp pairs
  metadata     — dict for transport-specific hints (priority, tags, …)
  retention    — forever | 1y | 30d | ephemeral (inherits from channel)

Channel config contract
───────────────────────
  address        — comms:// URI; routing target
  direction      — READ_ONLY | WRITE_ONLY | READ_WRITE (access gate)
  delivery       — PULL | PUSH (retrieval model; PUSH reserved for future)
  notify         — bool; whether to trigger WebSocket broadcast
  retention      — default TTL (1y, 30d, ephemeral, forever)
  show_timestamp — bool; web UI renders HHMMSS prefix on author labels
                   (T-web-chat-timestamp-prefix, 2026-04-20)
  log_path       — optional file path; auto-derived from address if None

Addressing scheme
─────────────────
  comms://shared                 — broadcast to all attached agents
  comms://discord/<channel-id>   — Discord channel (Discord transport)
  comms://discord/webhook        — Discord webhook
  comms://model/<model-name>     — LLM inference request/response
  comms://igor/<instance-id>     — per-instance intra-Igor comms

Subscriber model
────────────────
  comms.subscribe(address, subscriber_id, callback)
  comms.unsubscribe(address, subscriber_id)

Subscribers get notified on every send() EXCEPT for messages whose
message.source matches their subscriber_id (source-skip rule in send()).
Callbacks are synchronous during send(); exceptions are caught and logged,
not propagated.

File logging
────────────
Non-ephemeral messages are appended to .conversation.log files (JSON-per-
line). Log path derived from channel address:
  comms://shared            → base_dir/shared.conversation.log
  comms://discord/dm-akien  → base_dir/discord--dm-akien.conversation.log
Custom log_path overrides derivation. Ephemeral messages skip logging.

Routing flow (send)
───────────────────
  1. Lock; channel and transport looked up
  2. Direction checked (reject WRITE_ONLY reads, READ_ONLY writes)
  3. Retention inherited from channel if not set on message
  4. channel.last_active updated
  5. transport.send() called (if configured)
  6. Message logged to file (unless ephemeral)
  7. Subscribers notified (source-skip)
  8. _message_count incremented
  9. Return success (delivered || no transport configured)

Rack integration
────────────────
CommsModule extends RackModule (lab/utility_closet/rack.py) and registers
with the UC service layer on startup. Provides health(), stop(), and
standard name/version/type for discovery. UC server manages the module
lifecycle.

KEY DECISIONS SHAPING THIS SUBSYSTEM
────────────────────────────────────
  D210  channel-pg-mirror — server._channel_append writes to Postgres
        channel_messages; MCP channel_read sees all Igor web replies
  D335  utility-closet-platform — UC is the shared agent platform;
        comms is platform-level infrastructure, not Igor-only

ENGRAM PORTION
──────────────
None yet. Comms is pure infrastructure. Future: PROC_CHANNEL_* habits
when subscription patterns stabilize.

If you want to change:
  - Available transports    — add/remove files in transports/
  - Default retention       — edit Channel.retention default in dataclass
  - Timestamp prefix format — edit utility_closet_server.py addMsg(), not
                               this file
  - Log file paths          — edit Channel.log_file_path() derivation
  - Subscriber dispatch     — edit send() loop (watch source-skip rule)
  - Transport routing       — edit register_channel(),
                               set_default_transport()

Provenance:
  T-uc-comms-module              — initial implementation, 2026-03-30
  T-uc-comms-default-channels    — shared + per-agent auto-create, 2026-04-18
  T-web-chat-timestamp-prefix    — show_timestamp field, 2026-04-20
"""

from __future__ import annotations

import logging
from lab.utility_closet.agent_base import get_logger
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from .rack import RackModule

log = get_logger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────


class Direction(Enum):
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    READ_WRITE = "read_write"


class Delivery(Enum):
    PULL = "pull"
    PUSH = "push"


# ── Message envelope ─────────────────────────────────────────────────────────


@dataclass
class ChannelMessage:
    """Standard envelope for every message through comms."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    channel: str = ""  # comms://shared, comms://model/claude-sonnet
    source: str = ""  # igor-wild-0001, ccmain, akien
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    content_type: str = "text/plain"  # text/plain, text/markdown, inference/request
    payload: str = ""
    reply_to: Optional[str] = None  # correlation ID for req/resp
    metadata: dict = field(default_factory=dict)
    retention: Optional[str] = (
        None  # forever, 1y, 30d, ephemeral — inherits from channel
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "source": self.source,
            "timestamp": self.timestamp,
            "content_type": self.content_type,
            "payload": self.payload,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
            "retention": self.retention,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ChannelMessage:
        return cls(
            id=d.get("id", uuid.uuid4().hex[:16]),
            channel=d.get("channel", ""),
            source=d.get("source", ""),
            timestamp=d.get("timestamp", datetime.now().isoformat()),
            content_type=d.get("content_type", "text/plain"),
            payload=d.get("payload", ""),
            reply_to=d.get("reply_to"),
            metadata=d.get("metadata", {}),
            retention=d.get("retention"),
        )


# ── Channel definition ───────────────────────────────────────────────────────


@dataclass
class Channel:
    """Definition of a comms channel."""

    address: str  # comms://shared, comms://discord/general
    direction: Direction = Direction.READ_WRITE
    delivery: Delivery = Delivery.PULL
    notify: bool = False
    retention: str = "1y"  # default retention for messages
    show_timestamp: bool = True  # prefix "HHMMSS " on rendered author labels
    log_path: Optional[Path] = None  # auto-derived from address if None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())

    def log_file_path(self, base_dir: Path) -> Path:
        """Derive log file path from channel address."""
        if self.log_path:
            return self.log_path
        # comms://discord/dm-akien → discord--dm-akien.conversation.log
        name = self.address.replace("comms://", "").replace("/", "--")
        return base_dir / f"{name}.conversation.log"


# ── Transport base ───────────────────────────────────────────────────────────


class Transport:
    """
    Base class for comms transports. A transport handles the actual
    delivery mechanism for a channel (postgres, file, websocket, etc.).
    """

    def send(self, channel: Channel, message: ChannelMessage) -> bool:
        """Deliver a message. Returns True on success."""
        raise NotImplementedError

    def read(
        self,
        channel: Channel,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        """Read messages from the channel. Returns newest-first."""
        raise NotImplementedError

    def close(self) -> None:
        """Cleanup. Called on CommsModule shutdown."""
        pass


# ── CommsModule (rack shelf) ─────────────────────────────────────────────────


class CommsModule(RackModule):
    """
    Comms rack module — channel routing and message dispatch.

    Manages channels, routes messages to transports, notifies subscribers.
    Registers as a rack module with health reporting.
    """

    def __init__(self, log_base_dir: Optional[Path] = None, log_dir=None):
        super().__init__(
            name="comms",
            version="0.1.0",
            module_type="service",
            capabilities=["channel_routing", "message_dispatch"],
            log_dir=log_dir,
        )
        self._channels: dict[str, Channel] = {}
        self._transports: dict[str, Transport] = {}  # channel_address → transport
        self._default_transport: Optional[Transport] = None
        self._subscribers: dict[str, list[tuple[str, Callable]]] = (
            {}
        )  # channel → [(sub_id, callback)]
        self._lock = threading.Lock()
        self._message_count = 0
        self._log_base_dir = log_base_dir

    # ── Channel management ───────────────────────────────────────────────

    def register_channel(
        self,
        channel: Channel,
        transport: Optional[Transport] = None,
    ) -> None:
        """Register a channel with optional specific transport."""
        with self._lock:
            self._channels[channel.address] = channel
            if transport:
                self._transports[channel.address] = transport
        log.info("Comms: registered channel %s", channel.address)

    def get_channel(self, address: str) -> Optional[Channel]:
        """Get a channel by address."""
        with self._lock:
            return self._channels.get(address)

    def list_channels(self) -> list[Channel]:
        """Return all registered channels."""
        with self._lock:
            return list(self._channels.values())

    def set_default_transport(self, transport: Transport) -> None:
        """Set the default transport for channels without a specific one."""
        self._default_transport = transport

    # ── Messaging ────────────────────────────────────────────────────────

    def send(self, message: ChannelMessage) -> bool:
        """
        Send a message to its channel. Routes to the channel's transport
        and notifies subscribers.
        """
        with self._lock:
            channel = self._channels.get(message.channel)
            if channel is None:
                log.warning("Comms: send to unknown channel %s", message.channel)
                return False
            if channel.direction == Direction.READ_ONLY:
                log.warning(
                    "Comms: cannot send to read-only channel %s", message.channel
                )
                return False
            transport = self._transports.get(message.channel, self._default_transport)
            subscribers = list(self._subscribers.get(message.channel, []))

        # Inherit retention from channel if not set on message
        if message.retention is None:
            message.retention = channel.retention

        # Update channel last_active
        channel.last_active = message.timestamp

        # Route to transport
        delivered = False
        if transport:
            try:
                delivered = transport.send(channel, message)
            except Exception as exc:
                log.error("Comms: transport error on %s: %s", message.channel, exc)

        # Log to conversation file
        if self._log_base_dir and channel.retention != "ephemeral":
            self._log_to_file(channel, message)

        # Notify subscribers (skip the source — don't notify yourself)
        for sub_id, callback in subscribers:
            if sub_id != message.source:
                try:
                    callback(message)
                except Exception as exc:
                    log.warning("Comms: subscriber %s error: %s", sub_id, exc)

        self._message_count += 1
        return delivered or not transport  # success if no transport configured

    def read(
        self,
        channel_address: str,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        """Read messages from a channel via its transport."""
        with self._lock:
            channel = self._channels.get(channel_address)
            if channel is None:
                return []
            if channel.direction == Direction.WRITE_ONLY:
                return []
            transport = self._transports.get(channel_address, self._default_transport)

        if transport is None:
            return []
        try:
            return transport.read(channel, limit, since)
        except Exception as exc:
            log.error("Comms: read error on %s: %s", channel_address, exc)
            return []

    # ── Subscriptions ────────────────────────────────────────────────────

    def subscribe(
        self,
        channel_address: str,
        subscriber_id: str,
        callback: Callable[[ChannelMessage], None],
    ) -> str:
        """
        Subscribe to messages on a channel. Returns subscription ID.
        Callback is called for each message (except from the subscriber itself).
        """
        with self._lock:
            if channel_address not in self._subscribers:
                self._subscribers[channel_address] = []
            self._subscribers[channel_address].append((subscriber_id, callback))
        return subscriber_id

    def unsubscribe(self, channel_address: str, subscriber_id: str) -> None:
        """Remove a subscription."""
        with self._lock:
            subs = self._subscribers.get(channel_address, [])
            self._subscribers[channel_address] = [
                (sid, cb) for sid, cb in subs if sid != subscriber_id
            ]

    # ── File logging ─────────────────────────────────────────────────────

    def _log_to_file(self, channel: Channel, message: ChannelMessage) -> None:
        """Append message to conversation log file (JSON-per-line)."""
        import json

        try:
            log_path = channel.log_file_path(self._log_base_dir)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(message.to_dict(), separators=(",", ":"))
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            log.warning("Comms: log write failed for %s: %s", channel.address, exc)

    # ── Auto-creation ────────────────────────────────────────────────────

    def ensure_channel(
        self,
        address: str,
        direction: Direction = Direction.READ_WRITE,
        delivery: Delivery = Delivery.PULL,
        notify: bool = True,
        retention: str = "1y",
        show_timestamp: bool = True,
        transport: Optional[Transport] = None,
    ) -> Channel:
        """
        Get or create a channel. If the address was seen before, returns
        the existing channel with its original config. Otherwise creates
        a new one. Used for auto-creation on agent connect.
        """
        existing = self.get_channel(address)
        if existing:
            return existing
        ch = Channel(
            address=address,
            direction=direction,
            delivery=delivery,
            notify=notify,
            retention=retention,
            show_timestamp=show_timestamp,
        )
        self.register_channel(ch, transport)
        return ch

    # ── RackModule interface ─────────────────────────────────────────────

    def health(self) -> dict:
        with self._lock:
            channel_count = len(self._channels)
            sub_count = sum(len(subs) for subs in self._subscribers.values())
        return {
            "online": True,
            "channels": channel_count,
            "subscriptions": sub_count,
            "messages_routed": self._message_count,
        }

    def stop(self) -> None:
        """Close all transports on shutdown."""
        with self._lock:
            transports = list(set(self._transports.values()))
            if self._default_transport and self._default_transport not in transports:
                transports.append(self._default_transport)
        for t in transports:
            try:
                t.close()
            except Exception as exc:
                log.warning("Comms: transport close error: %s", exc)
        log.info("Comms: stopped (%d messages routed)", self._message_count)
