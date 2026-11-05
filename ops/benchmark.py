"""Small local measurement, not a production capacity claim."""
import json
import os
import statistics
import sys
import time
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.test import Client, override_settings
from charts.engine import calculate
from charts.models import Chart
chart=Chart.objects.filter(is_active=True).first()
if not chart:
    raise SystemExit('Create an anonymous demo first.')
data=chart.revisions.get(revision=chart.revision).input
def measure(fn,n):
    values=[]
    for _ in range(n):
        start=time.perf_counter();fn();values.append((time.perf_counter()-start)*1000)
    ordered=sorted(values)
    return {'samples':n,'median_ms':round(statistics.median(values),2),'p95_ms':round(ordered[int(.95*(n-1))],2),'max_ms':round(max(values),2)}
browser=Client()
with override_settings(ALLOWED_HOSTS=['testserver'],SECURE_SSL_REDIRECT=False):
    calculation=measure(lambda:calculate(data,settings.EPHEMERIS_PATH),50)
    def render():
        response=browser.get(f'/c/{chart.public_token}/')
        if response.status_code!=200:
            raise RuntimeError('Unexpected response during benchmark.')
    rendering=measure(render,30)
report={'environment':'Local Windows development host, sequential requests, no network/TLS time','database':settings.DATABASES['default']['ENGINE'],'exact_calculation':calculation,'stored_chart_response':rendering,'production_capacity_claim':False}
(root/'docs/benchmark-result.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
