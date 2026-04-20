"""
comms.py — Channel routing, message envelopes, and transport dispatch.

Lt Uhura's console: all routing, no participation. Every message through
comms gets a standard envelope regardless of channel. Channels are
addressable via comms:// URIs and backed by pluggable transports.

T-uc-comms-module
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from .rack import RackModule

log = logging.getLogger(__name__)


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
