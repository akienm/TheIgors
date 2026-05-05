"""gmail_compose.py — ComposePage page object for Gmail compose window.

Implements the ComposePage interface specified in GmailFlow:
  .set_to(addr), .set_subject(subject), .set_body(body), .send() -> message_id

Selector stability notes:
  [aria-label="To"]          — ARIA label; survives CSS minification.
  [aria-label="Subject"]     — ARIA label; same stability.
  [aria-label="Message Body"] — ARIA label on the contenteditable compose area.
  [data-tooltip*="Send"]     — tooltip data attr; more stable than button class.
  data-message-id            — attribute on the sent-confirmation element.

send() returns the sent message id by reading the thread ID from the URL
after Gmail redirects to the sent message view. Falls back to empty string
if the redirect does not occur within the expected DOM change.

driver_override: inject a mock driver in tests.
"""

from __future__ import annotations

from typing import Any, Optional

from SWADL.engine.swadl_base_section import SWADLPageSection

_SEL_TO = '[aria-label="To"]'
_SEL_SUBJECT = '[aria-label="Subject"]'
_SEL_BODY = '[aria-label="Message Body"]'
_SEL_SEND = '[data-tooltip*="Send"]'

# After send Gmail appends ?compose=<id> or redirects to /#sent/<thread>.
# The most reliable post-send signal is the compose window disappearing;
# thread id comes from URL fragment or a data attribute on the sent row.
_URL_SENT_MARKER = "#sent"


class ComposePage(SWADLPageSection):
    """Gmail compose window page object.

    Pass ``driver_override`` in tests to inject a mock selenium driver.
    """

    def __init__(
        self,
        name: str = "ComposePage",
        driver_override: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, **kwargs)
        self._driver_override = driver_override

    @property
    def _drv(self) -> Any:
        return (
            self._driver_override if self._driver_override is not None else self.driver
        )

    def set_to(self, addr: str) -> None:
        from selenium.webdriver.common.by import By

        self._drv.find_element(By.CSS_SELECTOR, _SEL_TO).send_keys(addr)

    def set_subject(self, subject: str) -> None:
        from selenium.webdriver.common.by import By

        self._drv.find_element(By.CSS_SELECTOR, _SEL_SUBJECT).send_keys(subject)

    def set_body(self, body: str) -> None:
        from selenium.webdriver.common.by import By

        self._drv.find_element(By.CSS_SELECTOR, _SEL_BODY).send_keys(body)

    def send(self) -> str:
        """Click Send and return the sent thread id from the post-send URL.

        Gmail redirects to /#sent/<thread-id> after a successful send.
        Parses the fragment; returns empty string if parsing fails so
        callers can treat a blank id as a signal to retry or warn.
        """
        from selenium.webdriver.common.by import By

        self._drv.find_element(By.CSS_SELECTOR, _SEL_SEND).click()
        return self._extract_sent_id()

    def _extract_sent_id(self) -> str:
        url = self._drv.current_url or ""
        if _URL_SENT_MARKER in url:
            fragment = url.split("#", 1)[-1]
            # fragment shape: "sent" or "sent/<thread-id>"
            parts = fragment.split("/", 1)
            if len(parts) == 2:
                return parts[1]
        return ""
