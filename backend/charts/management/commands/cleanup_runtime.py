import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.management import call_command
from charts.models import RateBucket

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        RateBucket.objects.filter(window__lt=int(time.time())//60-1440).delete()
        # Submission keys intentionally remain for durable idempotency.
        call_command('clearsessions')
        self.stdout.write('Expired sessions and old limiter buckets removed.')
