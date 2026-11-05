import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from charts.engine import verify_files
class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.DEBUG or settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
            raise CommandError('Production requires DEBUG=false and PostgreSQL.')
        if os.getenv('SWISSEPH_LICENSE_MODE') != 'AGPL' or os.getenv('LICENSE_ACKNOWLEDGED') != 'yes':
            raise CommandError('Confirm AGPL with SWISSEPH_LICENSE_MODE=AGPL and LICENSE_ACKNOWLEDGED=yes.')
        if not settings.SOURCE_URL.startswith('https://'):
            raise CommandError('SOURCE_URL must point users to the corresponding source for this deployed version.')
        verify_files(settings.EPHEMERIS_PATH)
        self.stdout.write('Production preflight passed.')
