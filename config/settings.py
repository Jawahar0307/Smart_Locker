"""
Django settings for Smart Storage Locker Management System.

This module contains all configuration for the Django project including
database, cache, authentication, logging, and REST framework settings.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

# =============================================================================
# CORE SETTINGS
# =============================================================================

BASE_DIR: Path = Path(__file__).resolve().parent.parent

SECRET_KEY: str = config('SECRET_KEY', default='django-insecure-dev-key')

DEBUG: bool = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS: list[str] = config(
    'ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv()
)

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS: list[str] = [
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',

    # Local apps
    'users.apps.UsersConfig',
    'lockers.apps.LockersConfig',
    'reservations.apps.ReservationsConfig',
]

MIDDLEWARE: list[str] = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF: str = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION: str = 'config.wsgi.application'

# =============================================================================
# DATABASE
# =============================================================================
# Render provides a DATABASE_URL environment variable for managed PostgreSQL.
# Falls back to SQLite for local development.

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')
    if DB_ENGINE == 'django.db.backends.sqlite3':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': DB_ENGINE,
                'NAME': config('DB_NAME', default='smart_locker_db'),
                'USER': config('DB_USER', default='postgres'),
                'PASSWORD': config('DB_PASSWORD', default='postgres'),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default='5432'),
                'OPTIONS': {
                    'connect_timeout': 5,
                },
            }
        }

# =============================================================================
# CUSTOM USER MODEL
# =============================================================================

AUTH_USER_MODEL: str = 'users.User'

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
]

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE: str = 'en-us'
TIME_ZONE: str = 'UTC'
USE_I18N: bool = True
USE_TZ: bool = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL: str = 'static/'
STATIC_ROOT: str = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE: str = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD: str = 'django.db.models.BigAutoField'

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '100/minute',
    },
}

# =============================================================================
# SIMPLE JWT
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# =============================================================================
# CACHE – Redis (with LocMemCache fallback for local dev)
# =============================================================================

REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')
USE_REDIS = config('USE_REDIS', default=False, cast=bool)

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': 60,
        }
    }
else:
    # Fallback: Django's in-memory cache (works without Redis)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'smart-locker-cache',
            'TIMEOUT': 60,
        }
    }

# =============================================================================
# CORS SETTINGS
# =============================================================================

CORS_ALLOW_ALL_ORIGINS: bool = DEBUG
CORS_ALLOWED_ORIGINS: list[str] = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# =============================================================================
# RENDER / PRODUCTION SETTINGS
# =============================================================================

RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# DRF SPECTACULAR (API DOCUMENTATION)
# =============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Smart Storage Locker Management System API',
    'DESCRIPTION': (
        'A comprehensive backend API for managing smart storage lockers. '
        'Supports user registration, JWT authentication, locker management, '
        'reservation handling, and Redis-cached availability lookups.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Authentication', 'description': 'User registration, login, and token management'},
        {'name': 'Lockers', 'description': 'Locker CRUD and availability'},
        {'name': 'Reservations', 'description': 'Locker reservation management'},
    ],
}

# =============================================================================
# LOGGING – Structured JSON for Kibana/ELK Integration
# =============================================================================

LOG_DIR: str = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
            'rename_fields': {
                'asctime': 'timestamp',
                'levelname': 'level',
                'name': 'logger',
            },
        },
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'file_json': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.json.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
            'level': 'INFO',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.json.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'json',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_json', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console', 'file_json', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'lockers': {
            'handlers': ['console', 'file_json', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'reservations': {
            'handlers': ['console', 'file_json', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_json', 'error_file'],
        'level': 'INFO',
    },
}
