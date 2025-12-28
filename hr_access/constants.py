# hr_access/constants.py
from django.conf import settings


SITE_ADMIN_GROUP_NAME = 'Site Admin'
GLOBAL_ADMIN_GROUP_NAME = 'Global Admin'
USER_GROUPS = [SITE_ADMIN_GROUP_NAME, GLOBAL_ADMIN_GROUP_NAME]


RESERVED_USERNAMES = {
    # auth/admin-ish
    "admin", "administrator", "root", "sysadmin", "staff", "mod", "moderator",
    "owner", "operator", "security", "support", "help", "service", "system", "home",
    "official",

    # comms + billing
    "billing", "payments", "refunds", "account_get_orders", "account", "accounts", "merch"

    # email-like handles people try
    "noreply", "no-reply", "donotreply", "do-not-reply", "mail", "mailer", "postmaster", "email", "message",

    # common route-ish collisions
    "login", "logout", "account_signup", "register", "settings", "profile", "api",
    "static", "media",

    # URL routes
    "shop", "shows", "merch", "cart", "checkout", "carousel", "quotes", "claims", "manage", "sidebar",
    "password", "post-purchase", "list", "about", "__debug__", "user", "live", "payment", "password-reset", "reset",
    "__reload__", "past", "webhooks",
}
