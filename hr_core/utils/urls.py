# hr_core/utils/urls.py

from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest


def _external_base_url_for_request() -> str:
    """
    Only use EXTERNAL_BASE_URL when USE_NGROK is enabled.
    Otherwise, fall back to request.build_absolute_uri so LAN/dev hosts work.
    """
    if getattr(settings, "USE_NGROK", False):
        base = (getattr(settings, "EXTERNAL_BASE_URL", "") or "").strip()
        return base.rstrip("/")
    return ""


def build_external_absolute_url(request: HttpRequest | None, path: str, *, query: dict | None = None) -> str:
    if not path.startswith("/"):
        path = "/" + path

    qs = f"?{urlencode(query)}" if query else ""
    base = _external_base_url_for_request()

    if base:
        return f"{base}{path}{qs}"

    if request is None:
        raise ValueError("Request is required when USE_NGROK is False.")

    return request.build_absolute_uri(f"{path}{qs}")
