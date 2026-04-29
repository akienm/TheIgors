"""
discord.py — Discord transport for comms channels (T-uc-channel-migration).

Bridges comms://discord/* channels to the existing discord_bot module.
Send routes through discord_bot.send(). Read is not supported (Discord
messages arrive via the listener queue, not polling).

Channel address format:
    comms://discord/<channel_id>       — send to a specific Discord channel
    comms://discord/webhook            — send via webhook (if configured)

The discord_bot module handles chunking (1900 char limit), webhook
fallback, reconnection, and forensic logging.
"""

from __future__ import annotations

import logging
from lab.utility_closet.agent_base import get_logger
import re
from typing import Optional

from ..comms import Channel, ChannelMessage, Transport

logger = get_logger(__name__)

# Pattern to extract channel ID from comms address
_CHANNEL_ID_RE = re.compile(r"comms://discord/(\d+)$")


def _extract_channel_id(address: str) -> Optional[int]:
    """Extract Discord channel ID from comms address."""
    m = _CHANNEL_ID_RE.match(address)
    if m:
        return int(m.group(1))
    return None


class DiscordTransport(Transport):
    """
    Transport that sends messages via the Discord bot.

    Write-only: Discord inbound messages arrive via the network listener,
    not through comms.read(). This transport handles the outbound path.
    """

    def __init__(self):
        super().__init__()
        self._bot = None
        self._send_count = 0

    def _get_bot(self):
        """Lazy-load the discord bot module."""
        if self._bot is None:
            try:
                from wild_igor.igor.network.discord_bot import discord_bot

                self._bot = discord_bot
            except ImportError:
                logger.debug("discord_bot not available")
                self._bot = False  # sentinel: tried and failed
        return self._bot if self._bot is not False else None

    def send(self, channel: Channel, message: ChannelMessage) -> bool:
        """Send a message to a Discord channel."""
        bot = self._get_bot()
        if bot is None:
            logger.warning("DiscordTransport: bot not available")
            return False

        channel_id = _extract_channel_id(channel.address)
        if channel_id is None:
            # Try webhook path
            if "webhook" in channel.address:
                return self._send_webhook(bot, message)
            logger.warning(
                "DiscordTransport: cannot parse channel ID from %s",
                channel.address,
            )
            return False

        text = message.payload or ""
        if not text:
            return False

        try:
            bot.send(channel_id, text)
            self._send_count += 1
            return True
        except Exception as exc:
            logger.warning("DiscordTransport send failed: %s", exc)
            return False

    def _send_webhook(self, bot, message: ChannelMessage) -> bool:
        """Send via Discord webhook if configured."""
        try:
            if hasattr(bot, "_send_via_webhook"):
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't await in sync context — queue it
                    bot.send(0, message.payload)
                    return True
            return False
        except Exception:
            return False

    def read(
        self,
        channel: Channel,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        """Discord transport is write-only. Inbound arrives via listener."""
        return []

    def close(self) -> None:
        """Bot lifecycle is managed by Igor, not the transport."""
        pass
