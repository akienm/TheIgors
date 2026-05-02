"""
File: web_chat.py
Purpose: Page object for localhost:8080 Igor web chat UI.

Defines selectors and controls for the chat interface to enable
SWADL-based automated testing of message sending and reply reception.
"""

from SWADL.engine.swadl_constants import VALIDATE_VISIBLE
from SWADL.engine.swadl_control import SWADLControl
from SWADL.engine.swadl_base_section import SWADLPageSection


class WebChatPage(SWADLPageSection):
    """Page object for Igor's web chat UI at localhost:8080."""

    def __init__(self, name="WebChatPage", test_data=None, **kwargs):
        """Initialize chat page with selectors for input, send button, and message list."""
        if test_data is None:
            test_data = {}
        super().__init__(name=name, test_data=test_data, **kwargs)
        self.url = "http://localhost:8080"

        # TODO: selectors below are unverified guesses — never opened the
        # actual chat UI source. First live run will likely need to update
        # them to match real DOM. See ticket T-web-chat-swadl-regression.

        # Input field where the user types a message. Placeholder-substring
        # match is more stable than positional/index selectors when the UI
        # changes layout.
        self.message_input = SWADLControl(
            name="message_input",
            parent=self,
            selector='input[placeholder*="message"]',
            validation={VALIDATE_VISIBLE: True},
        )

        # Form submit button — assumed standard <button type="submit">
        # within the chat input form.
        self.send_button = SWADLControl(
            name="send_button",
            parent=self,
            selector='button[type="submit"]',
            validation={VALIDATE_VISIBLE: True},
        )

        # Container for all messages. data-testid is the most refactor-stable
        # hook (survives CSS class renames) IF the UI exposes one.
        self.message_list = SWADLControl(
            name="message_list",
            parent=self,
            selector='[data-testid="message-list"]',
            validation={VALIDATE_VISIBLE: True},
        )

        # Individual message bubbles inside the list — count delta is how
        # the flow detects a new reply landing.
        self.message_items = SWADLControl(
            name="message_items",
            parent=self,
            selector='[data-testid="message-item"]',
        )

        self.validate_loaded_queue = [self.message_input, self.send_button]
