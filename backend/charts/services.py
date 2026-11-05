import hashlib
import json
from django.conf import settings
from django.db import transaction, IntegrityError
from .engine import calculate
from .models import Client, Chart, ChartRevision, AuditEvent, Submission, token
from .search import normalize
from .presentation import build_presentation_v1

class Conflict(ValueError):
    pass

def save_chart(form, actor, chart_id=None):
    d = form.cleaned_data
    existing = Submission.objects.filter(key=d['key'], actor=actor).select_related('chart').first()
    if existing:
        if existing.chart_id:
            return existing.chart
        raise Conflict('This submission has already been processed.')
    if not chart_id and not d['allow_duplicate'] and Client.objects.filter(search_name=normalize(d['internal_name']), chart__revisions__input__date=d['date'].isoformat()).exists():
        raise Conflict('Possible duplicate. Confirm “allow duplicate” to create a separate client.')
    data = form.birth_data()
    result = calculate(data, settings.EPHEMERIS_PATH)
    presentation = build_presentation_v1(result, d['language'])
    fingerprint = hashlib.sha256(json.dumps({'input': data, 'result': result, 'language':d['language'], 'presentation':presentation}, sort_keys=True).encode()).hexdigest()
    try:
        with transaction.atomic():
            Submission.objects.create(key=d['key'], actor=actor)
            if chart_id:
                chart = Chart.objects.select_for_update().select_related('client').get(pk=chart_id)
                if chart.revision != d['revision']:
                    raise Conflict('Another administrator changed this chart. Reload before saving.')
                client = chart.client
                chart.revision += 1
            else:
                client = Client()
                chart = Chart(client=client)
            client.internal_name = d['internal_name']
            client.internal_notes = d['internal_notes']
            client.save()
            chart.display_name = d['display_name'] or d['internal_name']
            chart.language = d['language']
            chart.save()
            ChartRevision.objects.create(chart=chart, revision=chart.revision, input=data, place_search=normalize(data['place']), result=result, language=d['language'], presentation=presentation, fingerprint=fingerprint, actor=actor, reason=d['reason'])
            AuditEvent.objects.create(actor=actor, chart_uuid=chart.pk, action='update' if chart_id else 'create', revision=chart.revision)
            Submission.objects.filter(key=d['key']).update(chart=chart)
            return chart
    except IntegrityError:
        existing = Submission.objects.filter(key=d['key'], actor=actor).select_related('chart').first()
        if existing and existing.chart_id:
            return existing.chart
        raise

def chart_action(chart_id, action, actor):
    with transaction.atomic():
        chart = Chart.objects.select_for_update().get(pk=chart_id)
        AuditEvent.objects.create(actor=actor, chart_uuid=chart.pk, action=action, revision=chart.revision)
        if action == 'delete':
            chart.client.delete()
            return None
        if action == 'rotate':
            chart.public_token = token()
        elif action == 'toggle':
            chart.is_active = not chart.is_active
        else:
            raise ValueError('Unsupported action')
        chart.save()
        return chart
