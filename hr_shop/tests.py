import logging

from django.test import SimpleTestCase

from hr_core.utils.unified_logging_core import reset_request_id, set_request_id
from hr_shop.unified_logging import log_event


class LoggingTests(SimpleTestCase):
    def test_log_event_includes_request_id_and_redacts(self):
        logger = logging.getLogger("hr_shop.tests")
        token = set_request_id("req-123")

        with self.assertLogs("hr_shop.tests", level="INFO") as captured:
            log_event(
                logger,
                logging.INFO,
                "checkout.test_event",
                email="user@example.com",
                token="secret-token",
                meta={"phone": "555-0100", "nickname": "ok"},
            )

        reset_request_id(token)

        output = "\n".join(captured.output)
        self.assertIn("event=checkout.test_event", output)
        self.assertIn("request_id=req-123", output)
        self.assertIn("**redacted**", output)
        self.assertNotIn("user@example.com", output)
        self.assertNotIn("secret-token", output)
