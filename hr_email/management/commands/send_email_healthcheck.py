import os

from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from hr_email.provider_settings import AVAILABLE_PROVIDERS, get_email_config


class Command(BaseCommand):
    help = "Send a test email through each SMTP provider to verify delivery."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="recipient",
            help="Email address to receive the test message (or set EMAIL_HEALTHCHECK_RECIPIENT).",
        )
        parser.add_argument(
            "--provider",
            choices=(*AVAILABLE_PROVIDERS, "all"),
            default="all",
            help="Run the check for a single provider or all configured providers.",
        )

    def handle(self, *args, **options):
        recipient = options["recipient"] or os.environ.get("EMAIL_HEALTHCHECK_RECIPIENT")
        provider_choice = options["provider"]

        if not recipient:
            raise CommandError("Provide a recipient via --to or EMAIL_HEALTHCHECK_RECIPIENT.")

        providers = AVAILABLE_PROVIDERS if provider_choice == "all" else (provider_choice,)
        sent_any = False
        errors = []

        for provider in providers:
            config = get_email_config()
            host = f"{config['host']}:{config['port']}"

            missing = []
            if not config["user"]:
                missing.append("EMAIL_HOST_USER")
            if not config["password"]:
                missing.append("EMAIL_HOST_PASSWORD")

            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{provider}] Skipping send (missing {' & '.join(missing)}). "
                        f"Set provider-specific vars like {provider.upper()}_EMAIL_HOST_USER or global EMAIL_HOST_USER."
                    )
                )
                continue

            self.stdout.write(f"[{provider}] Sending to {recipient} via {host} (TLS={config['use_tls']}, SSL={config['use_ssl']})")
            connection = get_connection(
                backend=config["backend"],
                host=config["host"],
                port=config["port"],
                username=config["user"],
                password=config["password"],
                use_tls=config["use_tls"],
                use_ssl=config["use_ssl"],
            )

            message = EmailMessage(
                subject=f"[Hella] SMTP health check via {provider} @ {timezone.now().isoformat(timespec='seconds')}",
                body="\n".join(
                    [
                        f"This is an automated SMTP health check using the {provider} configuration.",
                        f"Host: {host}",
                        f"TLS enabled: {config['use_tls']}",
                        f"SSL enabled: {config['use_ssl']}",
                        "",
                        "If you received this, SMTP connectivity is working.",
                    ]
                ),
                from_email=config["from_email"],
                to=[recipient],
                connection=connection,
            )

            try:
                message.send(fail_silently=False)
                sent_any = True
                self.stdout.write(self.style.SUCCESS(f"[{provider}] Test email sent to {recipient}"))
            except Exception as exc:  # pragma: no cover - surfaced as a CommandError
                errors.append(f"{provider}: {exc}")

            if errors:
                raise CommandError("One or more providers failed: " + "; ".join(errors))

            if not sent_any:
                raise CommandError("No messages were sent. Provide credentials and try again.")

            self.stdout.write(self.style.SUCCESS("Email health check complete."))
