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
    
    # Add Railway-specific domains for health checks and internal routing
    railway_hosts = [
        "healthcheck.railway.app",  # Railway health check domain
        "railway.app",              # Railway base domain
        ".railway.app",             # Railway wildcard domain
        "*.railway.app",            # Alternative wildcard syntax
        "127.0.0.1",                # Localhost
        "localhost",                # Localhost name
    ]
    
    hosts.extend(railway_hosts)
    
    # Add Railway internal domains if deployment ID exists
    if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
        deployment_id = os.environ['RAILWAY_DEPLOYMENT_ID']
        railway_internal = [
            f"{deployment_id}.railway.internal",
            f"{deployment_id}-production.railway.internal",
            f"{deployment_id}-development.railway.internal",
        ]
        hosts.extend(railway_internal)
    
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
        origins.extend([origin.strip()
                       for origin in additional_origins.split(",")])

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
    "users",  # Move users before master_data to resolve potential dependencies
    "master_data",
    "django_filters",
    "coreapi",
    "drf_spectacular",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "main.middleware.WorkspaceMiddleware",  # Add workspace middleware after auth
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


# Railway-specific database configuration
def get_railway_db_config():
    """Get database configuration optimized for Railway deployment."""
    base_config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_database_name(),
        "USER": os.environ["PGUSER"],
        "PASSWORD": os.environ["PGPASSWORD"],
        "HOST": os.environ["PGHOST"],
        "PORT": os.environ["PGPORT"],
        "OPTIONS": {
            "application_name": f"tux-backend-{CLIENT_SUBDOMAIN}",
            # Railway-optimized connection options with enhanced reliability
            "connect_timeout": 180,  # Extended timeout for Railway startup
            "server_side_binding": True,
            "sslmode": "prefer",  # Prefer SSL but allow fallback
            "keepalives_idle": 300,
            "keepalives_interval": 30,
            "keepalives_count": 3,
            # PostgreSQL settings for Railway reliability
            "options": (
                "-c statement_timeout=180s "
                "-c lock_timeout=120s "
                "-c idle_in_transaction_session_timeout=600s "
                "-c tcp_keepalives_idle=300 "
                "-c tcp_keepalives_interval=30 "
                "-c tcp_keepalives_count=3 "
                "-c log_disconnections=on "
                "-c log_connections=on"
            ),
        },
        "CONN_MAX_AGE": 0,  # No connection reuse during deployment
        "CONN_HEALTH_CHECKS": True,
        "ATOMIC_REQUESTS": True,
        "TEST": {
            "NAME": f"test_{get_database_name()}",
        },
    }
    
    # Special handling for Railway deployment phase
    if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
        # During deployment, use even more conservative settings
        base_config["OPTIONS"]["connect_timeout"] = 300  # 5 minutes for deployment
        base_config["OPTIONS"]["options"] += " -c log_min_duration_statement=5000"
        # Add deployment-specific connection retry logic
        base_config["OPTIONS"]["keepalives_idle"] = 600
        base_config["OPTIONS"]["keepalives_interval"] = 60
    
    return base_config

DATABASES = {
    "default": get_railway_db_config()
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
# Use lazy loading for authentication to avoid circular imports
def get_rest_framework_settings():
    """Get REST Framework settings with lazy imports."""
    return {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'users.authentication.CustomJWTAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
        'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],

        # API Versioning
        'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
        'DEFAULT_VERSION': 'v1',
        'ALLOWED_VERSIONS': ['v1', 'v2'],
        'VERSION_PARAM': 'version',
    }

# REST Framework configuration with circular import protection
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],

    # API Versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'VERSION_PARAM': 'version',

    # Throttling for rate limiting (production settings - more strict)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users: 100 requests per hour
        'user': '1000/hour',  # Authenticated users: 1000 requests per hour
        'auth': '5/minute',  # Authentication endpoint: 5 attempts per minute
        'token_refresh': '10/minute',  # Token refresh: 10 per minute
        'registration': '3/hour',  # Registration: 3 per hour
        'login_attempt': '5/minute',  # Per-user login attempts: 5 per minute
    },
}

# DJOSER settings
DJOSER = {
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': False,
    'ACTIVATION_URL': 'activation/{uid}/{token}',
    'SEND_CONFIRMATION_EMAIL': False,
    'USER_CREATE_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_RETYPE': False,
    'TOKEN_MODEL': None,
    'SERIALIZERS': {
        'user_create': 'users.serializers.UserCreateSerializer',
        'user': 'users.serializers.UserSerializer',
        'current_user': 'users.serializers.UserSerializer',
        'user_delete': 'users.serializers.UserDeleteSerializer',
    }
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
# DRF Spectacular Settings
# ────────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Tux API',
    'DESCRIPTION': 'Tux API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SECURITY_DEFINITIONS': {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        },
    },
    'SECURITY': [
        {'BearerAuth': []},
    ],
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
# Additional CORS settings to handle preflight requests
CORS_PREFLIGHT_MAX_AGE = 86400
CORS_EXPOSE_HEADERS = []

# ────────────────────────────────────────────────────────────────
# Static files - Railway optimized
# ────────────────────────────────────────────────────────────────
STATIC_URL = "static/"

# Only include static directories if they exist
staticfiles_dirs = []
if (BASE_DIR / "static").exists():
    staticfiles_dirs.append(BASE_DIR / "static")
STATICFILES_DIRS = staticfiles_dirs

# Railway static files configuration with fallback paths
def get_static_root():
    """Get appropriate static root path for Railway deployment."""
    # Try Railway-specific paths in order of preference
    railway_paths = [
        "/opt/railway/staticfiles",
        "/app/staticfiles", 
        str(BASE_DIR / "staticfiles"),
        "/tmp/staticfiles"
    ]
    
    # In Railway environment, use the first writable path
    if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
        for path in railway_paths:
            try:
                os.makedirs(path, exist_ok=True)
                if os.access(path, os.W_OK):
                    return path
            except (OSError, PermissionError):
                continue
    
    # Fallback to project directory
    fallback = str(BASE_DIR / "staticfiles")
    os.makedirs(fallback, exist_ok=True)
    return fallback

STATIC_ROOT = get_static_root()

# ────────────────────────────────────────────────────────────────
# WhiteNoise Configuration for Static Files
# ────────────────────────────────────────────────────────────────
# WhiteNoise settings for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MANIFEST_STRICT = False

# Additional WhiteNoise settings for better performance
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = [
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico', 'woff', 'woff2', 'ttf', 'eot'
]

# ────────────────────────────────────────────────────────────────
# Security / SSL  ‹★›
# ────────────────────────────────────────────────────────────────
# Railway terminates TLS and forwards HTTP with header X-Forwarded-Proto=https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # ‹★›

# SSL settings with health check exemption
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^health/$']  # Exempt health check from SSL redirect
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
        'security': {
            'format': '{levelname} {asctime} SECURITY: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'security',
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
            'level': 'DEBUG' if os.environ.get('RAILWAY_DEPLOYMENT_ID') else 'ERROR',
            'propagate': False,
        },
        'django.db.backends.postgresql': {
            'handlers': ['console'],
            'level': 'DEBUG' if os.environ.get('RAILWAY_DEPLOYMENT_ID') else 'WARNING',
            'propagate': False,
        },
        'master_data': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'security': {
            'handlers': ['security_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# ────────────────────────────────────────────────────────────────
# Master Data Configuration
# ────────────────────────────────────────────────────────────────
MASTER_DATA_CONFIG = {
    # String regeneration settings
    'AUTO_REGENERATE_STRINGS': os.getenv('AUTO_REGENERATE_STRINGS', 'True').lower() == 'true',
    'STRICT_AUTO_REGENERATION': os.getenv('STRICT_AUTO_REGENERATION', 'False').lower() == 'true',
    'ENABLE_INHERITANCE_PROPAGATION': os.getenv('ENABLE_INHERITANCE_PROPAGATION', 'True').lower() == 'true',
    'MAX_INHERITANCE_DEPTH': int(os.getenv('MAX_INHERITANCE_DEPTH', '5')),
}

# ────────────────────────────────────────────────────────────────
# Email Configuration (Resend)
# ────────────────────────────────────────────────────────────────
# Email backend - using console for development, Resend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Resend API Configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# Email sender configuration
DEFAULT_FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@tuxonomy.com")

# Frontend URL for invitation links and email templates
FRONTEND_URL = os.environ.get(
    'FRONTEND_URL',
    f"https://{os.environ.get('FRONTEND_SUBDOMAIN', CLIENT_SUBDOMAIN)}.{os.environ.get('FRONTEND_DOMAIN', 'vercel.app')}"
)
