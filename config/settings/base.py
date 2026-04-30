from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECRET_KEY: never use the unsafe fallback in any non-dev environment.
# The development settings will keep DEBUG=True; production.py demands a real key.
SECRET_KEY = config("SECRET_KEY", default="unsafe-secret-key-for-dev")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # GDPR/auth: enables JWT blacklist on refresh-rotate + logout
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # Local
    "apps.accounts",
    "apps.grief",
    "apps.imports",
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default="sqlite:///db.sqlite3"),
        conn_max_age=600,
    ),
}

AUTH_USER_MODEL = "accounts.User"

# OWASP A07: stronger password policy. MinimumLength bumped from 8 -> 10.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Security headers (apply in every environment; HSTS lives in production.py) ─
SECURE_CONTENT_TYPE_NOSNIFF = True              # OWASP: X-Content-Type-Options: nosniff
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"                        # OWASP: defense against clickjacking
SECURE_BROWSER_XSS_FILTER = True                # legacy header; harmless on modern browsers

# Cap upload sizes to prevent memory-exhaustion DoS via giant Excel uploads.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB request body
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB per file
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# ── DRF ──────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Throttle anonymous (login/register) and authenticated traffic to slow brute force.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "1000/min",
        "login": "10/min",       # token endpoint (see SCOPED_THROTTLE in urls)
        "register": "5/min",     # very tight; abuse target
    },
}

# ── JWT ───────────────────────────────────────────────────────────────────────
# Rotation + blacklist gives us logout-on-refresh and detection of stolen refresh tokens.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),       # was 8h; tighter blast radius if stolen
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,                     # OWASP A07: refresh-token rotation
    "BLACKLIST_AFTER_ROTATION": True,                  # used refresh tokens go to blacklist
    "UPDATE_LAST_LOGIN": True,                         # last_login tracked for audit
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── OpenAPI / Swagger ─────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Grief Tracker API",
    "DESCRIPTION": "Logistics issue tracking system API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Logging: never log credentials / authorization headers ───────────────────
# Django's admin error mail filter strips passwords by default; below we also
# scope a dedicated logger that reminds us not to log raw payloads.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "concise": {"format": "{levelname} {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "concise"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"level": "WARNING", "propagate": True},
        "django.security": {"level": "WARNING", "propagate": True},
        # Audit logger used by accounts views — INFO so logins/erasure show up.
        "audit": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Sensible cookie defaults that don't break http://localhost. production.py
# tightens these further (Secure=True, SameSite=Strict, HSTS, etc.).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # React/JS reads csrftoken; HttpOnly would break that
CSRF_COOKIE_SAMESITE = "Lax"
