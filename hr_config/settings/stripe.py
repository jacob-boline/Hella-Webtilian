# hr_config/settings/stripe.py


from hr_common.security import secrets

STRIPE_SECRET_KEY = secrets.read_secret("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = secrets.read_secret("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLIC_KEY = secrets.read_secret("STRIPE_PUBLIC_KEY")
