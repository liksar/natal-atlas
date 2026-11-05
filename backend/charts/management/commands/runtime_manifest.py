import json
import platform
from importlib.metadata import version
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from charts.engine import RULES_VERSION, TEXT_VERSION, verify_files

class Command(BaseCommand):
    def handle(self,*args,**kwargs):
        with connection.cursor() as cursor:
            cursor.execute('SHOW server_version')
            postgres=cursor.fetchone()[0]
        self.stdout.write(json.dumps({'python':platform.python_version(),'postgresql':postgres,'packages':{n:version(n) for n in ['Django','pysweph','tzdata']},'rules':RULES_VERSION,'texts':TEXT_VERSION,'ephemeris_manifest':verify_files(settings.EPHEMERIS_PATH)},sort_keys=True))
