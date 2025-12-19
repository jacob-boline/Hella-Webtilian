import os
from unittest import mock

from django.test import SimpleTestCase

from hr_email.provider_settings import get_email_config


class ProviderSettingsTests(SimpleTestCase):
    def test_defaults_to_mailjet(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config = get_email_config()

        self.assertEqual(config["provider"], "mailjet")
        self.assertEqual(config["host"], "in-v3.mailjet.com")
        self.assertEqual(config["port"], 587)
        self.assertTrue(config["use_tls"])
        self.assertFalse(config["use_ssl"])

    # def test_zoho_override(self):
    #     with mock.patch.dict(os.environ, {"EMAIL_PROVIDER": "zoho"}, clear=True):
    #         config = get_email_config()
    #
    #     self.assertEqual(config["provider"], "zoho")
    #     self.assertEqual(config["host"], "smtp.zoho.com")
    #     self.assertEqual(config["port"], 465)
    #     self.assertFalse(config["use_tls"])
    #     self.assertTrue(config["use_ssl"])

    def test_prefers_provider_specific_env_when_requested(self):
        env = {
            "EMAIL_PROVIDER": "mailjet",
            "EMAIL_HOST": "global.example.com",
            "EMAIL_HOST_USER": "global-user",
            "EMAIL_HOST_PASSWORD": "global-pass",
            "MAILJET_EMAIL_HOST": "mailjet.example.com",
            "MAILJET_EMAIL_PORT": "2525",
            "MAILJET_EMAIL_USE_TLS": "false",
            "MAILJET_EMAIL_USE_SSL": "true",
            "MAILJET_EMAIL_HOST_USER": "mj-user",
            "MAILJET_EMAIL_HOST_PASSWORD": "mj-pass",
            "DEFAULT_FROM_EMAIL": "Sender <sender@example.com>",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = get_email_config(provider_override="mailjet", prefer_provider_specific=True)

        self.assertEqual(config["host"], "mailjet.example.com")
        self.assertEqual(config["port"], 2525)
        self.assertFalse(config["use_tls"])
        self.assertTrue(config["use_ssl"])
        self.assertEqual(config["user"], "mj-user")
        self.assertEqual(config["password"], "mj-pass")
        self.assertEqual(config["from_email"], "Sender <sender@example.com>")