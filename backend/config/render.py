"""Render-managed TLS and PostgreSQL deployment."""
import os
from urllib.parse import urlsplit, unquote

host = os.environ['RENDER_EXTERNAL_HOSTNAME']
os.environ['DJANGO_ALLOWED_HOSTS'] = host
os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = 'https://' + host
url = urlsplit(os.environ['DATABASE_URL'])
if url.scheme not in ('postgres', 'postgresql') or not url.hostname:
    raise ValueError('A PostgreSQL DATABASE_URL is required.')
os.environ.update(POSTGRES_DB=unquote(url.path.lstrip('/')),
                  POSTGRES_USER=unquote(url.username or ''),
                  POSTGRES_PASSWORD=unquote(url.password or ''),
                  POSTGRES_HOST=url.hostname, POSTGRES_PORT=str(url.port or 5432))
commit = os.environ.get('RENDER_GIT_COMMIT', '')
os.environ['SOURCE_URL'] = 'https://github.com/liksar/natal-atlas/tree/' + (commit or 'codex/alpha-1')
from .preview import *
