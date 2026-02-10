# hr_config/settings/postgres.py


import dj_database_url

from hr_config.settings.common import require

db_url = require("DATABASE_URL")

if not (db_url.startswith("postgres://") or db_url.startswith("postgresql://")):
    raise RuntimeError("DATABASE_URL must start with 'postgres://' or 'postgresql://'")

DATABASES = {"default": dj_database_url.parse(db_url, conn_max_age=600, ssl_require=True)}
