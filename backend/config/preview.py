"""Isolated Windows alpha sharing profile; not the Linux production runtime."""
from .settings import *

if DEBUG or DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('Public alpha requires DEBUG=false and PostgreSQL.')
if LOCAL_PREVIEW_NULL_ORIGIN:
    raise ImproperlyConfigured('Opaque Origin development exceptions are prohibited in public alpha.')
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
# A temporary third-party hostname must never be submitted to the HSTS preload list.
SECURE_HSTS_PRELOAD = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_SECONDS = 3600
