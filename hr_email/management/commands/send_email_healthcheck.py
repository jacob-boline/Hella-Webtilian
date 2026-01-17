# hr_email/management/commands/send_email_healthcheck.py

import os

from django.core.management.base import BaseCommand, CommandError

from hr_email.service import EmailProviderError, send_app_email
from hr_email.provider_settings import AVAILABLE_PROVIDERS, get_provider


class Command(BaseCommand):
    help = "Send a test email using the same provider path the app uses."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="recipient",
            help="Email address to receive the test message (or set EMAIL_HEALTHCHECK_RECIPIENT).",
        )
        parser.add_argument(
            "--provider",
            choices=(*AVAILABLE_PROVIDERS, "default"),
            default="default",
            help="Provider to test. 'default' uses settings.EMAIL_PROVIDER.",
        )

    def handle(self, *args, **options):
        recipient = options["recipient"] or os.environ.get("EMAIL_HEALTHCHECK_RECIPIENT")
        if not recipient:
            raise CommandError("Provide a recipient via --to or EMAIL_HEALTHCHECK_RECIPIENT.")

        provider_choice = options["provider"]
        provider = get_provider(None if provider_choice == "default" else provider_choice)

        self.stdout.write(f"Sending healthcheck email using provider '{provider}' (as app would)…")

        try:
            result = send_app_email(
                to_emails=[recipient],
                subject="[Hella] Email health check",
                text_body="This is a test email sent via the app email service.",
                html_body="<p>This is a test email sent via the <b>app email service</b>.</p>",
                custom_id="email_healthcheck",
                provider_override=None if provider_choice == "default" else provider,
            )
        except EmailProviderError as exc:
            raise CommandError(f"Email healthcheck failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Email healthcheck sent to {recipient}. Result: {result}"))
