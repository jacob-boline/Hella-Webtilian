# hr_config/settings/stripe.py


from hr_common.security.secrets import read_secret

STRIPE_SECRET_KEY = read_secret("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = read_secret("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLIC_KEY = read_secret("STRIPE_PUBLIC_KEY")
