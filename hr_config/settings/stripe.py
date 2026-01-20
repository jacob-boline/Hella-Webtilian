# hr_config/settings/stripe.py


import os


STRIPE_SECRET_KEY     = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLIC_KEY     = os.getenv("STRIPE_PUBLIC_KEY", "")
