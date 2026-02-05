# hr_config/settings/vite.py
import os

from hr_config.settings.common import BASE_DIR, env_bool


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

DJANGO_VITE = {
    "default": {
        "dev_mode": env_bool("DJANGO_VITE_DEV_MODE", default=True),

        # These should be browser-reachable values (LAN IP when testing on phone)
        "dev_server_protocol": os.getenv("DJANGO_VITE_DEV_SERVER_PROTOCOL", "http"),
        "dev_server_host": os.getenv("DJANGO_VITE_DEV_SERVER_HOST", "localhost"),
        "dev_server_port": env_int("DJANGO_VITE_DEV_SERVER_PORT", 5173),

        "static_url_prefix": "",
        "manifest_path": BASE_DIR / "hr_core" / "static" / "hr_core" / "dist" / "manifest.json",
    }
}
