"""
Django production settings – loaded when DJANGO_SETTINGS_MODULE points here.
Designed for Railway (TLS terminated at the edge) + Vercel-hosted front-end.
"""

from pathlib import Path
from datetime import timedelta
import os
from os import getenv, path

# ────────────────────────────────────────────────────────────────
# Core paths / DEBUG
# ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = False

# Multi-tenant domain configuration
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "up.railway.app")
CLIENT_SUBDOMAIN = os.environ.get("CLIENT_SUBDOMAIN", "tux-prod")

# Dynamic allowed hosts for multi-tenant deployment


def get_allowed_hosts():
    hosts = [f".{BASE_DOMAIN}"]  # Wildcard for all subdomains

    # Add specific client subdomain if provided
    if CLIENT_SUBDOMAIN:
        hosts.append(f"{CLIENT_SUBDOMAIN}.{BASE_DOMAIN}")

    # Add any additional hosts from environment
    additional_hosts = os.environ.get("ADDITIONAL_ALLOWED_HOSTS", "")
    if additional_hosts:
        hosts.extend(additional_hosts.split(","))

    return hosts


ALLOWED_HOSTS = get_allowed_hosts()

# Dynamic CSRF trusted origins


def get_csrf_trusted_origins():
    origins = []

    # Add client-specific backend URL
    if CLIENT_SUBDOMAIN:
        origins.append(f"https://{CLIENT_SUBDOMAIN}.{BASE_DOMAIN}")

    # Add frontend URLs (could be different domain)
    frontend_domain = os.environ.get("FRONTEND_DOMAIN", "vercel.app")
    frontend_subdomain = os.environ.get("FRONTEND_SUBDOMAIN", CLIENT_SUBDOMAIN)

    if frontend_subdomain:
        origins.append(f"https://{frontend_subdomain}.{frontend_domain}")

    # Add any additional origins from environment
    additional_origins = os.environ.get("ADDITIONAL_CSRF_ORIGINS", "")
    if additional_origins:
        origins.extend(additional_origins.split(","))

    return origins


CSRF_TRUSTED_ORIGINS = get_csrf_trusted_origins()

AUTH_USER_MODEL = "users.UserAccount"
AUTH_COOKIE = "access"

# ────────────────────────────────────────────────────────────────
# Installed apps / middleware
# ────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    'djoser',
    "master_data",
    "django_filters",
    "users",
    "coreapi"
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "main.urls"

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

WSGI_APPLICATION = "main.wsgi.application"

# ────────────────────────────────────────────────────────────────
# Database (Railway injects env vars: PGHOST, PGPORT, PGUSER …)
# ────────────────────────────────────────────────────────────────
# Multi-tenant database configuration


def get_database_name():
    base_db = os.environ["PGDATABASE"]
    client_id = os.environ.get("CLIENT_ID", "")

    # Option 1: Separate database per client
    if client_id and os.environ.get("USE_CLIENT_DATABASE", "false").lower() == "true":
        return f"{base_db}_{client_id}"

    # Option 2: Same database (use tenant filtering in models)
    return base_db


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     get_database_name(),
        "USER":     os.environ["PGUSER"],
        "PASSWORD": os.environ["PGPASSWORD"],
        "HOST":     os.environ["PGHOST"],
        "PORT":     os.environ["PGPORT"],
        "OPTIONS": {
            "application_name": f"tux-backend-{CLIENT_SUBDOMAIN}",
        },
        "CONN_MAX_AGE": 300,  # 5 minutes
    }
}

# ────────────────────────────────────────────────────────────────
# Password validation / default PK type
# ────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ────────────────────────────────────────────────────────────────
# REST Framework / JWT
# ────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # 'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    # 'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],

    # API Versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'VERSION_PARAM': 'version',
}

# DJOSER settings
DJOSER = {
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': False,
    'ACTIVATION_URL': 'activation/{uid}/{token}',
    'SEND_CONFIRMATION_EMAIL': False,
    'USER_CREATE_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_RETYPE': False,
    'TOKEN_MODEL': None
}

AUTH_COOKIE = "access"
AUTH_COOKIE_ACCESS_MAX_AGE = 60 * 5
AUTH_COOKIE_REFRESH_MAX_AGE = 60 * 60 * 24
AUTH_COOKIE_SECURE = getenv("AUTH_COOKIE_SECURE", "True") == "True"
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_SAMESITE = 'None'

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
}

# ────────────────────────────────────────────────────────────────
# CORS
# ────────────────────────────────────────────────────────────────
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
# Dynamic CORS allowed origins (same as CSRF for consistency)
CORS_ALLOWED_ORIGINS = get_csrf_trusted_origins()
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ────────────────────────────────────────────────────────────────
# Static files
# ────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ────────────────────────────────────────────────────────────────
# Security / SSL  ‹★›
# ────────────────────────────────────────────────────────────────
# Railway terminates TLS and forwards HTTP with header X-Forwarded-Proto=https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # ‹★›

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ────────────────────────────────────────────────────────────────
# Internationalisation
# ────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ────────────────────────────────────────────────────────────────
# Logging Configuration
# ────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',  # Log database errors
            'propagate': False,
        },
        'master_data': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
