"""
or_chat.py — Stateful multi-turn LLM chat channel.

A layer on top of InferenceTransport that makes channels chattable:
  1. Caller sends a plain text/plain message (the user's turn).
  2. Transport stores the message, then assembles a multi-turn prompt
     from the channel's recent scrollback (newest N messages, oldest first).
  3. Prompt goes through the inference gateway.
  4. Response is stored back on the channel as source=inference-gateway.

Channel URI convention: `comms://or-chat/<model-or-purpose>/<session-id>`.

System prompt: stored as the first message on the channel with
content_type="chat/system" and source="system". The transport reads it
on every turn and pins it at the top of the assembled prompt; it is
never trimmed by the windowing policy.

Window trimming (MVP):
- Char-budget based, not token-budget. Conservative default: 16000 chars
  (roughly 4000 tokens, well inside every current model's window).
- Drop oldest first. System prompt pinned.
- Future: token-aware trim per model (needs gateway-level tokenizer access).

T-uc-chattable-llm-channel.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..comms import Channel, ChannelMessage, Transport
from .inference import (
    CT_REQUEST,
    CT_RESPONSE,
    INFERENCE_URI_PREFIX,
    InferenceTransport,
)

log = logging.getLogger(__name__)


OR_CHAT_URI_PREFIX = "comms://or-chat/"
CT_SYSTEM = "chat/system"
CT_USER = "chat/user"
CT_ASSISTANT = "chat/assistant"

# MVP window policy — characters, not tokens
DEFAULT_SCROLLBACK_BUDGET_CHARS = 16000
DEFAULT_SCROLLBACK_LIMIT = 50


class OrChatTransport(Transport):
    """Chat-channel transport. Wraps InferenceTransport so single-shot
    inference/request semantics still work if callers want them; the
    chat layer is additional behavior on top, triggered by content_type.

    Input:
      - content_type="chat/user" → assemble scrollback + gateway call + emit chat/assistant
      - content_type="chat/system" → stored as-is (sets/updates the system prompt)
      - other content_types → passthrough via underlying inference transport
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        scrollback_budget_chars: int = DEFAULT_SCROLLBACK_BUDGET_CHARS,
        scrollback_limit: int = DEFAULT_SCROLLBACK_LIMIT,
    ):
        self._inner = InferenceTransport(db_url)
        self._budget = scrollback_budget_chars
        self._limit = scrollback_limit

    # ── Transport interface ───────────────────────────────────────────────

    def send(self, channel: Channel, message: ChannelMessage) -> bool:
        if message.content_type == CT_USER:
            if not self._inner._store.send(channel, message):
                return False
            response = self._build_and_run(channel, message)
            if response is None:
                return False
            return self._inner._store.send(channel, response)

        # System prompts, pass-through, etc. — let inner transport handle
        return self._inner.send(channel, message)

    def read(
        self,
        channel: Channel,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        """Chat channels also unwrap inference-style envelopes (inherited
        behavior). For pure chat messages (chat/user, chat/assistant,
        chat/system), the content is plain text — no envelope.
        """
        return self._inner.read(channel, limit=limit, since=since)

    def close(self) -> None:
        self._inner.close()

    # ── Chat assembly ─────────────────────────────────────────────────────

    def _build_and_run(
        self,
        channel: Channel,
        user_msg: ChannelMessage,
    ) -> Optional[ChannelMessage]:
        """Assemble the prompt from scrollback, call gateway, wrap response."""
        scrollback = self._inner.read(channel, limit=self._limit)
        scrollback = list(reversed(scrollback))  # oldest-first for assembly
        system_prompt, turns = self._partition(scrollback)
        turns = self._trim_to_budget(turns, reserve_chars=len(user_msg.payload))
        prompt = self._render_prompt(system_prompt, turns)
        purpose = self._purpose_from_channel(channel.address)

        response_text = self._inner._run_inference(
            prompt=prompt,
            purpose=purpose,
            metadata=(user_msg.metadata or {}) | {"chat_session": channel.address},
        )
        return ChannelMessage(
            channel=channel.address,
            source="inference-gateway",
            content_type=CT_ASSISTANT,
            payload=response_text,
            reply_to=user_msg.id,
            metadata={
                "purpose": purpose,
                "gateway_tier": self._inner._last_tier(),
                "scrollback_turns": len(turns),
            },
            retention=user_msg.retention,
        )

    @staticmethod
    def _partition(
        scrollback: list[ChannelMessage],
    ) -> tuple[Optional[ChannelMessage], list[ChannelMessage]]:
        """Split scrollback into (system_prompt, chat_turns). Chat turns are
        the chat/user + chat/assistant messages in order. Non-chat messages
        are dropped from prompt assembly.
        """
        system_prompt: Optional[ChannelMessage] = None
        turns: list[ChannelMessage] = []
        for m in scrollback:
            if m.content_type == CT_SYSTEM:
                system_prompt = m  # last system wins (supports updates)
            elif m.content_type in (CT_USER, CT_ASSISTANT):
                turns.append(m)
        return system_prompt, turns

    def _trim_to_budget(
        self,
        turns: list[ChannelMessage],
        reserve_chars: int = 0,
    ) -> list[ChannelMessage]:
        """Drop oldest turns until total chars <= budget - reserve. reserve
        lets the caller carve out space for the new user message and
        response overhead.
        """
        budget = max(0, self._budget - reserve_chars)
        total = sum(len(m.payload) for m in turns)
        while turns and total > budget:
            dropped = turns.pop(0)
            total -= len(dropped.payload)
        return turns

    @staticmethod
    def _render_prompt(
        system_prompt: Optional[ChannelMessage],
        turns: list[ChannelMessage],
    ) -> str:
        """Simple alternating render: 'System: ...\\nUser: ...\\nAssistant: ...\\n...'.

        Models will accept this format via the gateway's existing string
        interface. Structured chat messages are a follow-up when the
        gateway grows a multi-message API.
        """
        parts: list[str] = []
        if system_prompt and system_prompt.payload:
            parts.append(f"System: {system_prompt.payload.strip()}")
        for m in turns:
            if m.content_type == CT_USER:
                parts.append(f"User: {m.payload.strip()}")
            elif m.content_type == CT_ASSISTANT:
                parts.append(f"Assistant: {m.payload.strip()}")
        parts.append("Assistant:")  # cue the model to continue
        return "\n\n".join(parts)

    @staticmethod
    def _purpose_from_channel(address: str) -> str:
        """Extract purpose from comms://or-chat/<purpose>/<session-id>.

        If the URI doesn't match the or-chat prefix, fall back to the part
        after comms://model/ (for back-compat). Empty string → 'default'.
        """
        if address.startswith(OR_CHAT_URI_PREFIX):
            tail = address.removeprefix(OR_CHAT_URI_PREFIX)
            return tail.split("/", 1)[0] or "default"
        if address.startswith(INFERENCE_URI_PREFIX):
            return address.removeprefix(INFERENCE_URI_PREFIX) or "default"
        return "default"
