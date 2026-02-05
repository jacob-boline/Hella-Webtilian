# hr_core/utils/urls.py

from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest


def _configured_base_url() -> str:
    """
    Canonical base URL for "external" links (emails, redirects, etc).
    If EXTERNAL_BASE_URL is set, use it always.
    (USE_NGROK can still be used for validation/policies elsewhere.)
    """
    base = (getattr(settings, "EXTERNAL_BASE_URL", "") or "").strip()
    return base.rstrip("/") if base else ""


def build_external_absolute_url(request: HttpRequest | None, path: str, *, query: dict | None = None) -> str:
    if not path.startswith("/"):
        path = "/" + path

    qs = f"?{urlencode(query)}" if query else ""
    base = _configured_base_url()

    if base:
        return f"{base}{path}{qs}"

    if request is None:
        raise ValueError("Request is required when EXTERNAL_BASE_URL is not set.")

    return request.build_absolute_uri(f"{path}{qs}")
