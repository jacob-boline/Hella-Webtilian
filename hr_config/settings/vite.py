# hr_config/settings/vite.py


import os

from hr_config.settings.common import BASE_DIR, env_bool

# DJANGO_VITE_DEV_MODE = os.environ.get("DJANGO_VITE_DEV_MODE", "True").strip().lower() == "true"

# The location where Vite writes the production build + manifest
DJANGO_VITE_ASSETS_PATH = BASE_DIR / "hr_core" / "static" / "hr_core" / "dist"
DJANGO_VITE_MANIFEST_PATH = DJANGO_VITE_ASSETS_PATH / "manifest.json"

if env_bool("DEBUG", default=True):
    static_url_prefix = ""
else:
    static_url_prefix = "hr_core/dist/"
# django-vite reads the manifest automatically when dev_mode=False.
# Keep dev_server_host/port optional for local dev workflow.
# DJANGO_VITE = {
#     "default": {
#         "dev_mode": env_bool('DJANGO_VITE_DEV_MODE', default=True),
#         "dev_server_host": os.environ.get("VITE_DEV_SERVER_HOST", "127.0.0.1"),
#         "dev_server_port": int(os.environ.get("VITE_DEV_SERVER_PORT", "5173")),
#         "static_url_prefix": static_url_prefix,
#         "manifest_path": str(DJANGO_VITE_MANIFEST_PATH)
#     }
# }


DJANGO_VITE = {
    "default": {
        "dev_mode": env_bool("DJANGO_VITE_DEV_MODE", default=True),
        "dev_server_protocol": "http",
        "dev_server_host": os.environ.get("VITE_DEV_SERVER_HOST", "127.0.0.1"),
        "dev_server_port": int(os.environ.get("VITE_DEV_SERVER_PORT", "5173")),
        "static_url_prefix": "/static/hr_core/dist/",  # prod prefix only
        "manifest_path": str(DJANGO_VITE_MANIFEST_PATH),
    }
}
