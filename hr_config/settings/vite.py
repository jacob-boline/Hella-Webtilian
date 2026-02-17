# hr_config/settings/vite.py

import os
from pathlib import Path

from hr_config.settings.base import STATIC_ROOT
from hr_config.settings.common import BASE_DIR, env_bool


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


DEV_MODE = env_bool("DJANGO_VITE_DEV_MODE", default=True)
SOURCE_MANIFEST = BASE_DIR / "hr_core" / "static" / "hr_core" / "dist" / "manifest.json"
COLLECTED_MANIFEST = Path(STATIC_ROOT) / "hr_core" / "dist" / "manifest.json"


DJANGO_VITE = {
    "default": {
        "dev_mode": DEV_MODE,

        "dev_server_protocol": os.getenv("DJANGO_VITE_DEV_SERVER_PROTOCOL", "http"),
        "dev_server_host": os.getenv("DJANGO_VITE_DEV_SERVER_HOST", "localhost"),
        "dev_server_port": env_int("DJANGO_VITE_DEV_SERVER_PORT", 5173),

        "static_url_prefix": "hr_core/dist",
        "manifest_path": SOURCE_MANIFEST if DEV_MODE else COLLECTED_MANIFEST
    }
}
