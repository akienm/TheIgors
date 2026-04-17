"""
memory.py — In-memory transport for comms channels.

Stores messages in a deque. Good for testing and ephemeral channels
that don't need persistence. Thread-safe.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Optional

from ..comms import Channel, ChannelMessage, Transport


class MemoryTransport(Transport):
    """In-memory message store backed by a bounded deque."""

    def __init__(self, max_messages: int = 1000):
        self._messages: dict[str, deque[ChannelMessage]] = {}
        self._max = max_messages
        self._lock = threading.Lock()

    def send(self, channel: Channel, message: ChannelMessage) -> bool:
        with self._lock:
            if channel.address not in self._messages:
                self._messages[channel.address] = deque(maxlen=self._max)
            self._messages[channel.address].append(message)
        return True

    def read(
        self,
        channel: Channel,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        with self._lock:
            msgs = list(self._messages.get(channel.address, []))
        if since:
            msgs = [m for m in msgs if m.timestamp > since]
        return list(reversed(msgs[-limit:]))

    def close(self) -> None:
        with self._lock:
            self._messages.clear()
