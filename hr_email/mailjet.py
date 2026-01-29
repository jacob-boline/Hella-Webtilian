# hr_email/mailjet.py

from collections.abc import Iterable
from functools import lru_cache

from django.conf import settings
from mailjet_rest import Client


class MailjetSendError(RuntimeError):
    """Raised when Mailjet returns a non-2xx response."""


@lru_cache(maxsize=1)
def get_mailjet_client() -> Client | None:
    api_key = getattr(settings, "MAILJET_API_KEY", None)
    api_secret = getattr(settings, "MAILJET_API_SECRET", None)
    if not api_key or not api_secret:
        return None
    return Client(auth=(api_key, api_secret), version="v3.1")


def send_mailjet_email(
    *,
    to: Iterable[dict],
    subject: str,
    text_part: str | None = None,
    html_part: str | None = None,
    from_email: dict | None = None,
    reply_to: dict | None = None,
    custom_id: str | None = None,
    sandbox_mode: bool | None = None,
) -> dict:
    client = get_mailjet_client()
    if client is None:
        raise MailjetSendError("Mailjet credentials are not configured.")

    sender = from_email or _as_address(getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@hellareptilian.com"))
    message = {
        "From": sender,
        "To": list(to),
        "Subject": subject,
        "TextPart": text_part,
        "HTMLPart": html_part,
    }
    if reply_to:
        message["ReplyTo"] = reply_to
    if custom_id:
        message["CustomID"] = custom_id
    if sandbox_mode:
        message["SandboxMode"] = True

    payload = {"Messages": [message]}
    resp = client.send.create(data=payload)
    if resp.status_code >= 300:
        raise MailjetSendError(f"Mailjet send failed ({resp.status_code}): {resp.json()}")
    return resp.json()


def send_email_healthcheck(to_email: str) -> dict:
    """
    Send a simple health-check email via Mailjet REST.
    """
    recipient = _as_address(to_email)
    return send_mailjet_email(
        to=[recipient],
        subject="Hella Reptilian email health check",
        text_part="This is a test email sent via Mailjet REST.",
        custom_id="email_healthcheck",
        sandbox_mode=False,
    )


def _as_address(raw: str) -> dict:
    """
    Convert a string like "Name <email@domain>" or "email@domain" to Mailjet's dict format.
    """
    if "<" in raw and ">" in raw:
        name, email = raw.split("<", 1)
        return {"Email": email.rstrip(">").strip(), "Name": name.strip()}
    return {"Email": raw, "Name": raw.split("@")[0]}
