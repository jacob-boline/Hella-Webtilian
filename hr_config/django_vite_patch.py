# hr_config/django_vite_patch.py

from __future__ import annotations

from urllib.parse import urljoin

from django_vite.core.asset_loader import DjangoViteAppClient


def patch_django_vite_dev_url() -> None:
    """
    django-vite 3.1.0 bug: in dev it incorrectly prepends settings.STATIC_URL to Vite dev URLs.
    Patch get_dev_server_url to join directly against the Vite dev server base.
    """

    def fixed_get_dev_server_url(self: DjangoViteAppClient, path: str) -> str:
        base = f"{self.dev_server_protocol}://{self.dev_server_host}:{self.dev_server_port}/"
        return urljoin(base, path.lstrip("/"))

    DjangoViteAppClient.get_dev_server_url = fixed_get_dev_server_url
