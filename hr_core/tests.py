import logging

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from hr_core.logging import log_event
from hr_core.middleware import RequestIdMiddleware
from hr_core.utils.logging import (
    REQUEST_ID_HEADER,
    get_request_id,
    redact_payload,
    reset_request_id,
    set_request_id,
)


class RequestIdMiddlewareTests(SimpleTestCase):
    def test_request_id_is_propagated_and_cleared(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_REQUEST_ID="req-123")
        captured = {}

        def get_response(req):
            captured["request_id"] = get_request_id()
            return HttpResponse("ok")

        middleware = RequestIdMiddleware(get_response)
        response = middleware(request)

        self.assertEqual(captured["request_id"], "req-123")
        self.assertEqual(response[REQUEST_ID_HEADER], "req-123")
        self.assertIsNone(get_request_id())


class RedactionTests(SimpleTestCase):
    def test_redact_payload_scrubs_sensitive_fields(self):
        payload = {
            "email": "user@example.com",
            "token": "secret-token",
            "profile": {
                "phone": "555-0100",
                "address": "123 Example St",
                "nickname": "hi",
            },
            "items": [
                {"name": "Item 1", "card_last4": "4242"},
                "ok",
            ],
        }

        redacted = redact_payload(payload)

        self.assertEqual(redacted["email"], "**redacted**")
        self.assertEqual(redacted["token"], "**redacted**")
        self.assertEqual(redacted["profile"]["phone"], "**redacted**")
        self.assertEqual(redacted["profile"]["address"], "**redacted**")
        self.assertEqual(redacted["profile"]["nickname"], "hi")
        self.assertEqual(redacted["items"][0]["card_last4"], "**redacted**")
        self.assertEqual(redacted["items"][1], "ok")


class LoggingTests(SimpleTestCase):
    def test_log_event_includes_request_id_and_redacts(self):
        logger = logging.getLogger("hr_core.tests")
        token = set_request_id("req-707")

        with self.assertLogs("hr_core.tests", level="INFO") as captured:
            log_event(
                logger,
                logging.INFO,
                "core.test_event",
                email="user@example.com",
                token="secret-token",
                meta={"phone": "555-0100", "nickname": "ok"},
            )

        reset_request_id(token)

        output = "\n".join(captured.output)
        self.assertIn("event=core.test_event", output)
        self.assertIn("request_id=req-707", output)
        self.assertIn("**redacted**", output)
        self.assertNotIn("user@example.com", output)
        self.assertNotIn("secret-token", output)
