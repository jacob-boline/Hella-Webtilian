# QNAP reverse proxy + Docker (production)

This checklist assumes QNAP terminates TLS and forwards traffic to the Docker
stack running `docker-compose.yml`.

## Compose defaults used for QNAP

- `docker-compose.yml` runs Nginx on port 80 and proxies to Django.
- The Django containers now use `hr_config.settings.prod_docker` so production
  settings can be driven entirely by environment variables (handy when the
  QNAP reverse proxy provides the TLS termination).

## Environment variables to provide

Secrets can be provided either as environment variables or Docker secrets
(`<NAME>_FILE`). The `read_secret()` helper checks `<NAME>_FILE` first, then
falls back to `<NAME>`.【F:hr_common/security/secrets.py†L1-L16】

### Required

**Core Django**
- `DJANGO_SECRET_KEY` (or `DJANGO_SECRET_KEY_FILE`) — required by `prod_docker`.【F:hr_config/settings/base.py†L11-L25】【F:hr_config/settings/prod_docker.py†L75-L76】
- `DEBUG` must be `False` (or unset, which defaults to `False`).【F:hr_config/settings/prod_docker.py†L11-L16】

**Database**
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`【F:docker-compose.yml†L12-L21】

**Email (Mailjet by default)**
- `EMAIL_HOST_USER` (or `EMAIL_HOST_USER_FILE`)
- `EMAIL_HOST_PASSWORD` (or `EMAIL_HOST_PASSWORD_FILE`)
- `MAILJET_API_KEY` (or `MAILJET_API_KEY_FILE`)
- `MAILJET_API_SECRET` (or `MAILJET_API_SECRET_FILE`)
  - Email credentials are required whenever `DEBUG=False`.【F:hr_config/settings/mailjet.py†L9-L22】【F:hr_config/settings/prod_docker.py†L71-L73】

**Stripe**
- `STRIPE_SECRET_KEY` (or `STRIPE_SECRET_KEY_FILE`)
- `STRIPE_WEBHOOK_SECRET` (or `STRIPE_WEBHOOK_SECRET_FILE`)
- `STRIPE_PUBLIC_KEY` (or `STRIPE_PUBLIC_KEY_FILE`)【F:hr_config/settings/stripe.py†L4-L8】

**Host / domain**
- `ALLOWED_HOSTS` (comma-separated)
- `CSRF_TRUSTED_ORIGINS` (comma-separated, include `https://hellareptilian.com`)
- `SITE_URL` (e.g. `https://hellareptilian.com`)【F:hr_config/settings/prod_docker.py†L19-L30】

### Recommended for QNAP reverse proxy

- `SECURE_SSL_REDIRECT` (`True` once QNAP is forwarding `X-Forwarded-Proto: https`)
- `CSRF_COOKIE_SECURE` (`True` once HTTPS is confirmed)
- `SESSION_COOKIE_SECURE` (`True` once HTTPS is confirmed)【F:hr_config/settings/prod_docker.py†L40-L44】

### Optional (defaults are already set in settings)

**Email defaults**
- `DEFAULT_FROM_EMAIL`
- `EMAIL_PROVIDER`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`【F:hr_config/settings/mailjet.py†L9-L17】

**Proxy header tweaks**
- `SECURE_PROXY_SSL_HEADER_NAME`
- `SECURE_PROXY_SSL_HEADER_VALUE`
- `USE_X_FORWARDED_HOST`【F:hr_config/settings/prod_docker.py†L36-L39】

**Redis (defaults to `redis:6379`)**
- `REDIS_HOST`
- `REDIS_PORT`【F:hr_config/settings/prod_docker.py†L52-L54】

**Vite**
- `DJANGO_VITE_DEV_MODE` (set `false` for production)【F:hr_config/settings/vite.py†L12-L24】

**S3 storage (only if you intend to use `hr_storage` backends)**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`【F:hr_storage/conf.py†L5-L18】

## Notes for QNAP reverse proxy

- Ensure the QNAP reverse proxy forwards `Host`, `X-Forwarded-For`, and
  `X-Forwarded-Proto: https`.
- Turn on the HTTPS-only settings above once the forwarded proto is correct
  to avoid redirect loops.
