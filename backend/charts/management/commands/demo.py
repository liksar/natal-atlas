import uuid
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.urls import reverse
from charts.forms import ChartForm
from charts.services import save_chart

class Command(BaseCommand):
    help = 'Create a synthetic, anonymous demo chart in development only.'
    def add_arguments(self, parser):
        parser.add_argument('--dense', action='store_true')
        parser.add_argument('--approximate', action='store_true')
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demo creation is development-only.')
        user, created = get_user_model().objects.get_or_create(username='_demo_author', defaults={'is_active': False})
        if created:
            user.set_unusable_password();user.save()
        form = ChartForm({'key': uuid.uuid4(), 'revision': 0, 'internal_name': 'Synthetic demo', 'display_name': 'Олександра · Demo', 'language':'uk', 'date': '2020-01-12' if options['dense'] else '1995-05-17', 'time': '14:30', 'time_mode': 'approximate' if options['approximate'] else 'exact', 'uncertainty_minutes':30 if options['approximate'] else None, 'place': 'Kyiv, Ukraine', 'latitude': 50.4501, 'longitude': 30.5234, 'timezone': 'Europe/Kyiv', 'reason': 'Anonymous demonstration; fictional person', 'allow_duplicate': True})
        if not form.is_valid():
            raise CommandError(str(form.errors))
        chart = save_chart(form, user)
        self.stdout.write(reverse('public-chart', args=[chart.public_token]))
