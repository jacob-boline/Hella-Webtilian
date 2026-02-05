# hr_config/settings/mailjet.py


import os

from hr_common.security.secrets import read_secret
from hr_config.settings.common import env_bool

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Hella Reptilian <mail@hellareptilian.com>")
EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "mailjet").strip().lower()
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "in-v3.mailjet.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
#
# MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY_FILE") or EMAIL_HOST_USER
# MAILJET_API_SECRET = os.environ.get("MAILJET_API_SECRET_FILE") or EMAIL_HOST_PASSWORD

EMAIL_HOST_USER = read_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = read_secret('EMAIL_HOST_PASSWORD')

MAILJET_API_KEY = read_secret('MAILJET_API_KEY')
MAILJET_API_SECRET = read_secret('MAILJET_API_SECRET')
