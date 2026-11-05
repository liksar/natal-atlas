import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT = BASE_DIR.parent
DEBUG = os.getenv('DJANGO_DEBUG', 'false').lower() == 'true'
LOCAL_PREVIEW_NULL_ORIGIN = os.getenv('LOCAL_PREVIEW_NULL_ORIGIN') == '1'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY; no default secret is provided.')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = list(filter(None, os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')))
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django_countries', 'charts']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.locale.LocaleMiddleware', 'django.middleware.common.CommonMiddleware', 'charts.csrf.LocalPreviewCsrfMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'charts.middleware.SecurityMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages', 'charts.i18n.context']}}]
if os.getenv('LOCAL_SQLITE') == '1':
    if not DEBUG:
        raise ImproperlyConfigured('LOCAL_SQLITE is restricted to development.')
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ROOT / 'dev.sqlite3'}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.getenv('POSTGRES_DB', 'natal'), 'USER': os.getenv('POSTGRES_USER', 'natal'), 'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''), 'HOST': os.getenv('POSTGRES_HOST', 'db'), 'PORT': os.getenv('POSTGRES_PORT', '5432'), 'CONN_MAX_AGE': 60}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': f'django.contrib.auth.password_validation.{name}'} for name in ['UserAttributeSimilarityValidator', 'MinimumLengthValidator', 'CommonPasswordValidator', 'NumericPasswordValidator']]
PASSWORD_HASHERS = ['django.contrib.auth.hashers.Argon2PasswordHasher', 'django.contrib.auth.hashers.PBKDF2PasswordHasher']
LANGUAGE_CODE = 'uk'
LANGUAGES = [('en', 'English'), ('uk', 'Українська'), ('ru', 'Русский')]
TIME_ZONE = os.getenv('ADMIN_TIME_ZONE', 'Europe/Kyiv')
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = ROOT / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_SSL_REDIRECT = not DEBUG
# Gunicorn must only be reachable from the controlled Caddy network.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
EPHEMERIS_PATH = Path(os.getenv('EPHEMERIS_PATH', str(ROOT / 'data/ephe')))
SOURCE_URL = os.getenv('SOURCE_URL', '')
SOURCE_ARCHIVE = os.getenv('SOURCE_ARCHIVE', '')
APP_RELEASE = os.getenv('APP_RELEASE', '')
CONTACT_TEXT = os.getenv('CONTACT_TEXT', '')
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'null': {'class': 'logging.NullHandler'}}, 'loggers': {'django.request': {'handlers': ['null'], 'propagate': False}, 'django.server': {'handlers': ['null'], 'propagate': False}}}
