"""Idempotent bootstrap under a database lock, then start the WSGI server."""
import os
import sys
import json
import threading
import csv
import io
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.render')
import django
django.setup()
from django.core.management import call_command
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from charts.models import City

class Starting(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(503)
        self.end_headers()
        self.wfile.write(b'Preparing first deployment. Please retry shortly.')
    def log_message(self, *args):
        pass

# Render must discover a listening port while the initial dataset is imported.
# Readiness stays unsuccessful until bootstrap finishes.
starting = ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '10000'))), Starting)
threading.Thread(target=starting.serve_forever, daemon=True).start()

with connection.cursor() as cursor:
    cursor.execute('SELECT pg_advisory_lock(72165001)')
try:
    call_command('migrate', interactive=False)
    manifest = root / 'data-manifests/places.json'
    info = json.loads(manifest.read_text())
    version = info['dataset_version']
    with zipfile.ZipFile(root / info['archive']) as zipped, zipped.open(info['member']) as stream:
        expected = sum(1 for row in csv.reader(io.TextIOWrapper(stream, encoding='utf-8'), delimiter='\t') if len(row) >= 19 and row[17])
    if City.objects.filter(dataset_version=version).count() != expected:
        with transaction.atomic():
            call_command('import_places', manifest=str(manifest))
    users = get_user_model()
    if not users.objects.filter(username='alpha_admin').exists():
        users.objects.create_superuser('alpha_admin', '', os.environ['ALPHA_ADMIN_PASSWORD'])
    call_command('preflight')
finally:
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_unlock(72165001)')
    connection.close()
starting.shutdown()
starting.server_close()
os.chdir(root / 'backend')
os.execvp('gunicorn', ['gunicorn', 'config.wsgi:application', '--bind',
                      '0.0.0.0:' + os.environ.get('PORT', '10000'),
                      '--workers', '1', '--threads', '1', '--timeout', '120',
                      '--access-logfile', '/dev/null'])
