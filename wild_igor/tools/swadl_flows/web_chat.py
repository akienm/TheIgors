"""
File: web_chat.py
Purpose: Flow object for Igor web chat interaction.

Exposes send_message_and_read_reply() for posting messages and waiting for
Igor-authored responses with configurable timeout.
"""

import time
from SWADL.engine.swadl_base_flow import SWADLBaseFlow
from wild_igor.tools.swadl_pages.web_chat import WebChatPage


class WebChatFlow(SWADLBaseFlow):
    """Flow for interacting with Igor's web chat UI."""

    def __init__(self, name="WebChatFlow", **kwargs):
        """Initialize the chat flow with page object."""
        super().__init__(name=name, **kwargs)
        self.chat_page = WebChatPage()

    def send_message_and_read_reply(self, text, timeout_sec=120):
        """
        Post a message and wait for Igor's reply.

        Args:
            text: User message to send.
            timeout_sec: Maximum time to wait for reply (default 120s).

        Returns:
            Reply text from Igor, or empty string if timeout.
        """
        self.chat_page.load_page()
        self.chat_page.validate_loaded()

        initial_count = len(self.chat_page.message_items.get_elements())

        self.chat_page.message_input.set_value(value=text)
        self.chat_page.send_button.click()

        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            current_count = len(self.chat_page.message_items.get_elements())
            if current_count > initial_count + 1:
                new_messages = self.chat_page.message_items.get_elements()
                latest_message = new_messages[-1]
                reply_text = latest_message.text.strip()
                return reply_text

            time.sleep(1)

        return ""
