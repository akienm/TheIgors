"""gmail_inbox.py — InboxPage page object for Gmail.

HARD REQUIREMENT — browser profile:
  Gmail pages MUST run in Igor's pre-authenticated Chrome profile. Without
  it, Chrome opens a fresh unauthenticated session and hits the login wall.

  Set before creating any page or driver:
      from SWADL.engine.swadl_cfg import cfgdict
      from SWADL.engine.swadl_constants import SELENIUM_USER_DATA_DIR
      cfgdict[SELENIUM_USER_DATA_DIR] = IGOR_PROFILE_PATH

  Igor's profile on akiendelllinux:
      ~/.agent_datacenter/Igor-wild-0001/accounts/chrome_igor_profile

  Callers that skip this step will get a RuntimeError from load() rather
  than a silent unauthenticated session that looks like it worked.

Implements the InboxPage interface specified in GmailFlow:
  .load(), .open_compose(), .first_n_messages(n), .find_message(message_id)

Selector stability notes (see also gmail_message_ref.py):
  tr.zA       — minified Gmail row class; stable across standard builds,
                breaks under experimental UI reclasses. Most robust
                available without data-testid hooks.
  span.bog    — subject text; minified, same risk level as tr.zA.
  [email]     — from-address attribute; attribute selector, more stable
                than class selectors.
  .y2         — snippet text; minified, same risk level.
  data-legacy-thread-id — thread ID attribute on rows; "legacy" suggests
                          Google may remove it. Prefer when present; fall
                          back to row index if absent.

driver_override: inject a mock driver in tests. Production leaves it None
and uses SWADL's global driver via self.driver.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from SWADL.engine.swadl_base_section import SWADLPageSection

# Igor's pre-authenticated Chrome profile. Set cfgdict[SELENIUM_USER_DATA_DIR]
# to this path before creating the driver.
IGOR_PROFILE_PATH = str(
    Path.home() / ".agent_datacenter/Igor-wild-0001/accounts/chrome_igor_profile"
)

_INBOX_URL = "https://mail.google.com/mail/u/0/#inbox"

# Selector constants — centralised so a single change fixes all methods.
_SEL_COMPOSE = '[data-tooltip="Compose"]'
_SEL_MSG_ROWS = "tr.zA"
_SEL_SUBJECT = "span.bog"
_SEL_FROM = "[email]"
_SEL_SNIPPET = ".y2"
_ATTR_THREAD_ID = "data-legacy-thread-id"


class InboxPage(SWADLPageSection):
    """Gmail inbox page object.

    Requires Igor's Chrome profile to be configured in cfgdict before the
    driver starts — see module docstring. load() raises RuntimeError if the
    profile is not set, catching the silent-unauthenticated-session failure.

    Pass ``driver_override`` in tests to inject a mock selenium driver
    instead of relying on SWADL's global cfgdict driver.
    """

    def __init__(
        self,
        name: str = "InboxPage",
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

    def load(self) -> None:
        from SWADL.engine.swadl_cfg import cfgdict
        from SWADL.engine.swadl_constants import SELENIUM_USER_DATA_DIR

        if not cfgdict.get(SELENIUM_USER_DATA_DIR):
            raise RuntimeError(
                "InboxPage.load(): SELENIUM_USER_DATA_DIR not set in cfgdict. "
                "Gmail requires Igor's pre-authenticated Chrome profile. "
                f"Set cfgdict[SELENIUM_USER_DATA_DIR] = IGOR_PROFILE_PATH "
                f"before creating the driver. Igor's profile: {IGOR_PROFILE_PATH}"
            )
        self._drv.get(_INBOX_URL)

    def open_compose(self) -> "ComposePage":
        from selenium.webdriver.common.by import By

        from wild_igor.tools.swadl_pages.gmail_compose import ComposePage

        btn = self._drv.find_element(By.CSS_SELECTOR, _SEL_COMPOSE)
        btn.click()
        return ComposePage(driver_override=self._driver_override)

    def first_n_messages(self, n: int) -> list:
        from selenium.webdriver.common.by import By

        rows = self._drv.find_elements(By.CSS_SELECTOR, _SEL_MSG_ROWS)[:n]
        return [self._row_to_ref(row) for row in rows]

    def find_message(self, message_id: str) -> Any:
        from selenium.webdriver.common.by import By

        rows = self._drv.find_elements(By.CSS_SELECTOR, _SEL_MSG_ROWS)
        for row in rows:
            tid = row.get_attribute(_ATTR_THREAD_ID) or ""
            if tid == message_id:
                return self._row_to_ref(row)
        return None

    def _row_to_ref(self, row: Any) -> Any:
        from selenium.webdriver.common.by import By

        from wild_igor.tools.swadl_pages.gmail_message_ref import MessageRef

        def _text(sel: str) -> str:
            try:
                return row.find_element(By.CSS_SELECTOR, sel).text or ""
            except Exception:
                return ""

        def _attr(sel: str, attr: str) -> str:
            try:
                return row.find_element(By.CSS_SELECTOR, sel).get_attribute(attr) or ""
            except Exception:
                return ""

        return MessageRef(
            id=row.get_attribute(_ATTR_THREAD_ID) or "",
            subject=_text(_SEL_SUBJECT),
            from_addr=_attr(_SEL_FROM, "email") or _text(_SEL_FROM),
            snippet=_text(_SEL_SNIPPET),
            _row_element=row,
            _driver=self._drv,
        )
