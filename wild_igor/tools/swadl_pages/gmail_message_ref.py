"""gmail_message_ref.py — MessageRef page-side handle for a Gmail message.

Returned by InboxPage methods; callers receive plain-data MessageSummary
from the flow layer. MessageRef carries the live selenium element reference
and knows how to archive itself.

Selector stability note: archive action uses [aria-label="Archive"] which
is an ARIA attribute and survives CSS class minification. If Google A/B
tests the button label, this breaks — monitor on regressions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from wild_igor.tools.swadl_flows.gmail import MessageSummary

_ARCHIVE_BTN = '[aria-label="Archive"]'


@dataclass
class MessageRef:
    """Page-side handle for a single Gmail message row.

    Fields match the interface spec in GmailFlow. ``_row_element`` and
    ``_driver`` are selenium internals — not part of the public contract.
    """

    id: str
    subject: str
    from_addr: str
    snippet: str
    _row_element: Any = field(repr=False, default=None, compare=False)
    _driver: Any = field(repr=False, default=None, compare=False)

    def archive(self) -> None:
        """Open the message then click Archive.

        Two-step: click row to open → find Archive button → click.
        The button only reliably appears inside the open message view.
        """
        if self._row_element is not None:
            self._row_element.click()
        if self._driver is not None:
            from selenium.webdriver.common.by import By

            btn = self._driver.find_element(By.CSS_SELECTOR, _ARCHIVE_BTN)
            btn.click()

    def as_summary(self) -> "MessageSummary":
        from wild_igor.tools.swadl_flows.gmail import MessageSummary

        return MessageSummary(
            id=self.id,
            subject=self.subject,
            from_addr=self.from_addr,
            snippet=self.snippet,
        )
