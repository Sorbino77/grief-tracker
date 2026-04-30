"""
Production settings for Grief Tracker.

Loaded when DJANGO_SETTINGS_MODULE=config.settings.production. All security-
critical values come from environment variables — never commit secrets.

Required env vars:
    SECRET_KEY                 — must NOT be the dev fallback
    ALLOWED_HOSTS              — comma-separated, e.g. "grief.example.com"
    DATABASE_URL               — postgres://...
    CSRF_TRUSTED_ORIGINS       — comma-separated, e.g. "https://grief.example.com"
    CORS_ALLOWED_ORIGINS       — comma-separated; do NOT use "*"

Optional:
    SECURE_HSTS_SECONDS        — default 31536000 (1 year)
    SECURE_SSL_REDIRECT        — default True
"""
from decouple import Csv, config

from .base import *  # noqa: F401,F403

DEBUG = False

# Refuse to boot with the dev fallback in production.
if SECRET_KEY == "unsafe-secret-key-for-dev":  # noqa: F405
    raise RuntimeError(
        "SECRET_KEY is unset (or still the dev fallback). Set it in the environment "
        "before starting in production.",
    )

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be set in production.")

# ── HTTPS / TLS ──────────────────────────────────────────────────────────────
# Behind a TLS-terminating proxy (nginx, ALB, Cloudflare, etc.) Django needs
# this header to know the original request was https.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)

# HSTS: tell browsers to always use HTTPS for this domain. Only enable once
# you're sure HTTPS works for every subdomain you serve from.
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)

# ── Cookies ──────────────────────────────────────────────────────────────────
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Strict"

# Origins allowed to submit cross-origin POSTs that include the CSRF cookie.
# In production, your frontend(s) must be listed explicitly.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# ── CORS ─────────────────────────────────────────────────────────────────────
# Never use CORS_ALLOW_ALL_ORIGINS=True in production.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=False, cast=bool)

# ── Email (so error reports + password resets actually send) ─────────────────
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# Admins receive 5xx error emails (be careful with PII; consider Sentry instead).
ADMINS = [tuple(pair.split(":", 1)) for pair in config("DJANGO_ADMINS", default="", cast=Csv())]
