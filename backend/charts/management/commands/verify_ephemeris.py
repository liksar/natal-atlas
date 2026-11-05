from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from charts.engine import verify_files, CalculationError
class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            fingerprint = verify_files(settings.EPHEMERIS_PATH)
        except CalculationError as exc:
            raise CommandError(str(exc))
        self.stdout.write(f'Verified: {fingerprint}')
