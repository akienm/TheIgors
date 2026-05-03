"""gmail.py — Gmail flow object (T-gmail-flow-layer).

Workflow-first design (Akien 2026-05-03): this flow declares the spec for
what each Page must do; Pages get built LAST. Flows do routing only;
Pages and automations/tests do the hard work.

Domain methods Igor can invoke:
  send_email(to, subject, body)
  read_inbox(n)
  archive(message_id)

Each method composes calls against page objects via the Page interface
documented below. Pages can be injected at construction time — production
passes real Page objects; tests pass mocks (since pages haven't been
written yet — those are follow-on tickets per Page).

Browser profile (HARD requirement, per ticket scope):
  Tests and production must run in Akien's Igor browser profile, NOT the
  default. Set SELENIUM_USER_DATA_DIR before launching the driver. SWADL
  profile-support shipped 2026-05-03 (akienm/swadl@2347aa2) — set the
  env var via cfgdict[SELENIUM_USER_DATA_DIR] = "/path/to/profile".

Page interface (what each Page must expose):
  - InboxPage:
      .load() -> None
      .open_compose() -> ComposePage
      .first_n_messages(n) -> list[MessageRef]   # unread/read agnostic
      .find_message(message_id) -> MessageRef | None
  - ComposePage:
      .set_to(addr) -> None
      .set_subject(subject) -> None
      .set_body(body) -> None
      .send() -> str  # message_id of the sent message
  - MessageRef (return type):
      .id -> str
      .subject -> str
      .from_addr -> str
      .snippet -> str
      .archive() -> None

The interface is duck-typed (no abstract base) — Page implementers match
the shape; mocks return-value the methods. Adding new domain methods
requires extending this contract, not bypassing it.

Updated 2026-05-03.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from SWADL.engine.swadl_base_flow import SWADLBaseFlow


@dataclass
class MessageSummary:
    """Plain-data summary of a Gmail message returned by read_inbox.

    Distinct from MessageRef (which is a page-side handle) — flows return
    MessageSummary so callers don't have to depend on the page module's
    types. Pages translate their MessageRef → MessageSummary via
    .as_summary() when read_inbox is invoked.
    """

    id: str
    subject: str
    from_addr: str
    snippet: str


class GmailFlow(SWADLBaseFlow):
    """Routing-only flow for Gmail domain operations.

    Pages are injected at construction so tests pass mocks. Production
    passes real Page objects from wild_igor.tools.swadl_pages.gmail_inbox
    and gmail_compose (those follow-on tickets are not yet shipped).
    """

    def __init__(
        self,
        inbox_page: Optional[Any] = None,
        compose_page: Optional[Any] = None,
        name: str = "GmailFlow",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._inbox_page = inbox_page
        self._compose_page = compose_page

    # ── Domain methods ────────────────────────────────────────────────────

    def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email. Returns the sent message id.

        Routing: open compose page → fill fields → send → return id.
        Page contract: ComposePage.set_to / set_subject / set_body / send.
        """
        if self._compose_page is None:
            raise RuntimeError(
                "GmailFlow.send_email: compose_page not injected. Pass "
                "compose_page=<page> at construction (or a mock for testing)."
            )
        self._compose_page.set_to(to)
        self._compose_page.set_subject(subject)
        self._compose_page.set_body(body)
        return self._compose_page.send()

    def read_inbox(self, n: int = 10) -> list[MessageSummary]:
        """Read the first n inbox messages. Returns plain-data summaries.

        Routing: load inbox → fetch first_n_messages → translate refs to
        MessageSummary.
        Page contract: InboxPage.load / first_n_messages.
        """
        if self._inbox_page is None:
            raise RuntimeError("GmailFlow.read_inbox: inbox_page not injected.")
        if n < 0:
            raise ValueError(f"read_inbox(n={n}): n must be non-negative")
        self._inbox_page.load()
        refs = self._inbox_page.first_n_messages(n)
        return [
            MessageSummary(
                id=ref.id,
                subject=ref.subject,
                from_addr=ref.from_addr,
                snippet=ref.snippet,
            )
            for ref in refs
        ]

    def archive(self, message_id: str) -> bool:
        """Archive the message with the given id. Returns True on success.

        Routing: load inbox → find message → archive.
        Page contract: InboxPage.load / find_message; MessageRef.archive.
        """
        if self._inbox_page is None:
            raise RuntimeError("GmailFlow.archive: inbox_page not injected.")
        self._inbox_page.load()
        ref = self._inbox_page.find_message(message_id)
        if ref is None:
            return False
        ref.archive()
        return True
