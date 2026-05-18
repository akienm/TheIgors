"""
shim.py — Akien as an addressable rack entity.

Akien is not a daemon. This shim is a static identity record that gives
his web and Discord traffic a comms:// address (comms://akien/) the ADC
bus can route like any other device.

Data home: ~/.agent_datacenter/akien/  (inbox/, outbox/, ideas/ already exist)
Web routing: messages sent via the browser are wrapped as comms://akien/web
  by utility_closet_server before being appended to channel_messages.
Design rules: no-sqlite, no-TheIgors-imports.
"""

from __future__ import annotations

from pathlib import Path

_DATA_HOME = Path.home() / ".agent_datacenter" / "akien"

_IDENTITY: dict = {
    "id": "akien",
    "entity_type": "human",
    "address": "comms://akien/",
    "data_home": str(_DATA_HOME),
    "channels": {
        "inbox": "comms://akien/inbox",
        "outbox": "comms://akien/outbox",
        "ideas": "comms://akien/ideas",
        "web": "comms://akien/web",
    },
    "online": False,
}


class AkienShim:
    """Static identity shim for Akien on the ADC rack."""

    def who_am_i(self) -> dict:
        """Return the rack identity for Akien.

        Shape:
            id           — rack-unique device identifier
            entity_type  — "human" (not a daemon or agent)
            address      — comms:// address for routing
            data_home    — filesystem root for this device's state
            channels     — named comms:// sub-addresses
            online       — always False; Akien is not a process
        """
        return dict(_IDENTITY)


def who_am_i() -> dict:
    """Module-level convenience wrapper around AkienShim().who_am_i()."""
    return AkienShim().who_am_i()
