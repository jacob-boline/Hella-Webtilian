import logging

from django.test import SimpleTestCase, override_settings

from hr_core.utils.unified_logging_core import reset_request_id, set_request_id
from hr_email.unified_logging import log_event
from hr_email.provider_settings import get_email_config, get_mailjet_rest_config


class ProviderSettingsTests(SimpleTestCase):
    @override_settings(
        EMAIL_PROVIDER="mailjet",
        # Intentionally do NOT set EMAIL_HOST/PORT/TLS to ensure defaults apply.
        EMAIL_HOST_USER="user",
        EMAIL_HOST_PASSWORD="pass",
        DEFAULT_FROM_EMAIL="Sender <sender@example.com>",
    )
    def test_smtp_defaults_to_mailjet_provider_defaults(self):
        config = get_email_config()

        self.assertEqual(config["provider"], "mailjet")
        self.assertEqual(config["host"], "in-v3.mailjet.com")
        self.assertEqual(config["port"], 587)
        self.assertTrue(config["use_tls"])
        self.assertFalse(config["use_ssl"])

        self.assertEqual(config["user"], "user")
        self.assertEqual(config["password"], "pass")
        self.assertEqual(config["from_email"], "Sender <sender@example.com>")

    @override_settings(
        EMAIL_PROVIDER="mailjet",
        EMAIL_HOST="smtp.override.local",
        EMAIL_PORT=2525,
        EMAIL_USE_TLS=False,
        EMAIL_USE_SSL=True,
        EMAIL_HOST_USER="override-user",
        EMAIL_HOST_PASSWORD="override-pass",
        DEFAULT_FROM_EMAIL="Override <override@example.com>",
    )
    def test_smtp_respects_explicit_settings_over_defaults(self):
        config = get_email_config()

        self.assertEqual(config["host"], "smtp.override.local")
        self.assertEqual(config["port"], 2525)
        self.assertFalse(config["use_tls"])
        self.assertTrue(config["use_ssl"])
        self.assertEqual(config["user"], "override-user")
        self.assertEqual(config["password"], "override-pass")
        self.assertEqual(config["from_email"], "Override <override@example.com>")

    @override_settings(MAILJET_API_KEY=None, MAILJET_API_SECRET=None)
    def test_mailjet_rest_config_disabled_without_credentials(self):
        cfg = get_mailjet_rest_config()
        self.assertFalse(cfg["enabled"])
        self.assertFalse(cfg["api_key_set"])
        self.assertFalse(cfg["api_secret_set"])

    @override_settings(MAILJET_API_KEY="k", MAILJET_API_SECRET="s")
    def test_mailjet_rest_config_enabled_with_credentials(self):
        cfg = get_mailjet_rest_config()
        self.assertTrue(cfg["enabled"])
        self.assertTrue(cfg["api_key_set"])
        self.assertTrue(cfg["api_secret_set"])


class LoggingTests(SimpleTestCase):
    def test_log_event_includes_request_id_and_redacts(self):
        logger = logging.getLogger("hr_email.tests")
        token = set_request_id("req-202")

        with self.assertLogs("hr_email.tests", level="INFO") as captured:
            log_event(
                logger,
                logging.INFO,
                "email.test_event",
                email="user@example.com",
                token="secret-token",
                meta={"phone": "555-0100", "nickname": "ok"},
            )

        reset_request_id(token)

        output = "\n".join(captured.output)
        self.assertIn("event=email.test_event", output)
        self.assertIn("request_id=req-202", output)
        self.assertIn("**redacted**", output)
        self.assertNotIn("user@example.com", output)
        self.assertNotIn("secret-token", output)
