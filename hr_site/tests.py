import ast
import logging

from django.test import SimpleTestCase

from hr_core.utils.unified_logging_core import reset_request_id, set_request_id
from hr_site.unified_logging import log_event


class LoggingTests(SimpleTestCase):
    def test_log_event_includes_request_id_and_redacts(self):
        logger = logging.getLogger("hr_site.tests")
        token = set_request_id("req-505")

        with self.assertLogs("hr_site.tests", level="INFO") as captured:
            log_event(
                logger,
                logging.INFO,
                "site.test_event",
                email="user@example.com",
                token="secret-token",
                meta={"phone": "555-0100", "nickname": "ok"},
            )

        reset_request_id(token)

        output = "\n".join(captured.output)
        payload = ast.literal_eval(output.split(":", 2)[-1])
        self.assertEqual(payload["event"], "site.test_event")
        self.assertEqual(payload["request_id"], "req-505")
        self.assertEqual(payload["email"], "**redacted**")
        self.assertEqual(payload["token"], "**redacted**")
        self.assertEqual(payload["meta"]["phone"], "**redacted**")
        self.assertEqual(payload["meta"]["nickname"], "ok")
        self.assertNotIn("user@example.com", output)
        self.assertNotIn("secret-token", output)
