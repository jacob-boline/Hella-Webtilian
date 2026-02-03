# hr_config/settings/vite.py

from hr_config.settings.common import BASE_DIR, env_bool


DJANGO_VITE = {
    "default": {
        "dev_mode": env_bool("DJANGO_VITE_DEV_MODE", default=True),
        "dev_server_protocol": "http",
        "dev_server_host": "localhost",
        "dev_server_port": 5174,
        "static_url_prefix": "",
        "manifest_path": BASE_DIR / "hr_core" / "static" / "hr_core" / "dist" / "manifest.json"
    }
}
