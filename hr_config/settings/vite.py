# hr_config/settings/vite.py


import os
from hr_config.settings.common import BASE_DIR

DJANGO_VITE_DEV_MODE = os.environ.get("DJANGO_VITE_DEV_MODE", "True").strip().lower() == "true"

# The location where Vite writes the production build + manifest
DJANGO_VITE_ASSETS_PATH = BASE_DIR / "hr_core" / "static" / "hr_core" / "dist"
DJANGO_VITE_MANIFEST_PATH = DJANGO_VITE_ASSETS_PATH / "manifest.json"

# django-vite reads the manifest automatically when dev_mode=False.
# Keep dev_server_host/port optional for local dev workflow.
DJANGO_VITE = {
    "default": {
        "dev_mode": DJANGO_VITE_DEV_MODE,
        "dev_server_host": os.environ.get("VITE_DEV_SERVER_HOST", "127.0.0.1"),
        "dev_server_port": int(os.environ.get("VITE_DEV_SERVER_PORT", "5173")),
        "static_url_prefix": "hr_core/dist/",
        "manifest_path": str(DJANGO_VITE_MANIFEST_PATH)
    }
}
