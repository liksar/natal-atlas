"""Idempotent bootstrap under a database lock, then start the WSGI server."""
import os
import sys
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.render')
import django
django.setup()
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
from charts.models import City

with connection.cursor() as cursor:
    cursor.execute('SELECT pg_advisory_lock(72165001)')
try:
    call_command('migrate', interactive=False)
    manifest = root / 'data-manifests/places.json'
    version = json.loads(manifest.read_text())['dataset_version']
    if not City.objects.filter(dataset_version=version).exists():
        call_command('import_places', manifest=str(manifest))
    users = get_user_model()
    if not users.objects.filter(username='alpha_admin').exists():
        users.objects.create_superuser('alpha_admin', '', os.environ['ALPHA_ADMIN_PASSWORD'])
    call_command('preflight')
finally:
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_unlock(72165001)')
    connection.close()
os.chdir(root / 'backend')
os.execvp('gunicorn', ['gunicorn', 'config.wsgi:application', '--bind',
                      '0.0.0.0:' + os.environ.get('PORT', '10000'),
                      '--workers', '1', '--threads', '1', '--timeout', '120',
                      '--access-logfile', '/dev/null'])
