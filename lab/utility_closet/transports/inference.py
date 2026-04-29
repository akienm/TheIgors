"""
inference.py — Inference-as-channel transport.

MVP implementation: treats LLM calls as messages on a comms channel.

- Send an inference/request message → transport calls the inference gateway,
  stores both the request and the response in Postgres, emits the response
  as an inference/response message with the correlation ID in the payload.
- Read returns the full message history (requests + responses interleaved).

Channel address convention: `comms://model/<purpose-or-model-name>`.

The first pass uses the existing inference_gateway (same routing Igor uses
elsewhere); per-model channels that skip gateway routing are a follow-up.

Design notes (for the follow-up tickets):
- No schema migration yet — correlation ID and reply_to live in a JSON
  envelope inside the `content` column. When channel_messages grows a
  proper `reply_to` column + `msg_id` + `metadata` JSONB, move them out.
- Async response delivery (subscribe-and-await) is also follow-up. Today
  the transport is synchronous: send() blocks until the gateway returns.
- Per-model routing (e.g. comms://model/gemini-pro → Gemini only) will
  need a per-channel handler override on the gateway; MVP uses the
  purpose-based routing the gateway already implements.

T-uc-inference-channel (MVP).
"""

from __future__ import annotations

import json
import logging
from lab.utility_closet.agent_base import get_logger
import uuid
from typing import Optional

from ..comms import Channel, ChannelMessage, Transport
from .postgres import PostgresTransport

log = get_logger(__name__)


# Channel-address prefix convention
INFERENCE_URI_PREFIX = "comms://model/"

# content_type values on the wire
CT_REQUEST = "inference/request"
CT_RESPONSE = "inference/response"


def _wrap_payload(msg_id: str, text: str, reply_to: Optional[str] = None) -> str:
    """Encode correlation metadata into the content JSON envelope.

    Envelope shape: {"id": ..., "reply_to": ..., "text": ...}.
    Kept small and parseable so callers can extract the user-facing text with
    a single json.loads. When channel_messages gains proper correlation
    columns, delete this and drop the envelope.
    """
    return json.dumps(
        {"id": msg_id, "reply_to": reply_to, "text": text},
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _unwrap_payload(content: str) -> tuple[str, str, Optional[str]]:
    """Return (msg_id, text, reply_to). Tolerant of non-envelope strings."""
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "text" in data:
            return (
                data.get("id", ""),
                data.get("text", ""),
                data.get("reply_to"),
            )
    except Exception:
        pass
    # Plain-text fallback — legacy or non-inference messages in the channel
    return ("", content, None)


class InferenceTransport(Transport):
    """Thin transport: stores messages in Postgres, invokes the gateway on
    inference/request, emits inference/response with reply_to correlation.

    One gateway instance is reused across calls (lazy-built on first use).
    """

    def __init__(self, db_url: Optional[str] = None):
        super().__init__()
        self._store = PostgresTransport(db_url)
        self._gateway = None  # lazy

    # ── Gateway access ────────────────────────────────────────────────────

    def _get_gateway(self):
        if self._gateway is None:
            from wild_igor.igor.cognition.inference_gateway import get_gateway

            self._gateway = get_gateway()
        return self._gateway

    def _run_inference(self, prompt: str, purpose: str, metadata: dict) -> str:
        """Call the existing inference gateway. Returns response text or
        an error-tagged string so callers can distinguish success from
        failure without raising.

        T-inference-transport-make-context-signature (Pass-2 Area 5 Gap 1):
        make_context takes (is_background, is_user_turn, research_mode,
        complexity) — not purpose/metadata. Previously every call TypeError'd
        and the transport silently returned '[inference-error] ...'; whole
        comms://model/* surface was dead. purpose flows via gw.call's
        purpose_id; metadata has no corresponding channel in the gateway
        so we log it for traceability and drop it.
        """
        from wild_igor.igor.cognition.inference_gateway import make_context

        try:
            gw = self._get_gateway()
            complexity = "low"
            research_mode = False
            if metadata:
                complexity = str(metadata.get("complexity", complexity))
                research_mode = bool(metadata.get("research_mode", research_mode))
            ctx = make_context(
                research_mode=research_mode,
                complexity=complexity,
            )
            text = gw.call(purpose_id=purpose, prompt=prompt, ctx=ctx)
            return text or ""
        except Exception as exc:
            log.error("InferenceTransport: gateway call failed: %s", exc)
            return f"[inference-error] {type(exc).__name__}: {exc}"

    # ── Transport interface ───────────────────────────────────────────────

    def send(self, channel: Channel, message: ChannelMessage) -> bool:
        """Send a message. For inference/request, also invoke the gateway
        and emit an inference/response message back on the same channel.
        Non-inference messages are stored as-is (pass-through behavior).
        """
        # Wrap the request payload so correlation metadata is carried
        if message.content_type == CT_REQUEST:
            msg_id = message.id or uuid.uuid4().hex[:16]
            wrapped = _wrap_payload(msg_id, message.payload, message.reply_to)
            stored_request = ChannelMessage(
                id=msg_id,
                channel=message.channel,
                source=message.source,
                timestamp=message.timestamp,
                content_type=CT_REQUEST,
                payload=wrapped,
                reply_to=message.reply_to,
                metadata=message.metadata,
                retention=message.retention,
            )
            if not self._store.send(channel, stored_request):
                return False

            # Derive purpose from channel address (comms://model/<purpose>)
            purpose = channel.address.removeprefix(INFERENCE_URI_PREFIX) or "default"
            response_text = self._run_inference(
                prompt=message.payload,
                purpose=purpose,
                metadata=message.metadata or {},
            )
            response = ChannelMessage(
                channel=channel.address,
                source="inference-gateway",
                content_type=CT_RESPONSE,
                payload=_wrap_payload(
                    uuid.uuid4().hex[:16], response_text, reply_to=msg_id
                ),
                reply_to=msg_id,
                metadata={"purpose": purpose, "gateway_tier": self._last_tier()},
                retention=message.retention,
            )
            return self._store.send(channel, response)

        # Non-inference messages: plain pass-through to storage
        return self._store.send(channel, message)

    def read(
        self,
        channel: Channel,
        limit: int = 50,
        since: Optional[str] = None,
    ) -> list[ChannelMessage]:
        """Read message history. Unwraps inference envelopes so callers see
        plain text in `payload` (with correlation IDs intact on the message).
        """
        rows = self._store.read(channel, limit=limit, since=since)
        unwrapped = []
        for row in rows:
            if row.content_type in (CT_REQUEST, CT_RESPONSE):
                msg_id, text, reply_to = _unwrap_payload(row.payload)
                row.id = msg_id or row.id
                row.payload = text
                row.reply_to = reply_to
            unwrapped.append(row)
        return unwrapped

    def close(self) -> None:
        self._store.close()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _last_tier(self) -> str:
        """Best-effort last-tier read from the gateway. Empty string if the
        gateway never ran or the attribute is missing.
        """
        try:
            return getattr(self._gateway, "last_tier", "") or ""
        except Exception:
            return ""
