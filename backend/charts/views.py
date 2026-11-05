import uuid
from urllib.parse import urlsplit
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import connection, DatabaseError
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import translation
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from .models import Client, Chart, ChartRevision, City
from .forms import ChartForm
from .services import save_chart, chart_action, Conflict
from .engine import CalculationError, verify_files, BODIES, ASPECTS
from .i18n import WORDS, PLANETS, SIGNS, ASPECT_NAMES
from .texts import interpretation, house_text, aspect_text
from .errors import local_error
from .search import normalize

@require_GET
def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('clients')
    return render(request, 'home.html')

@staff_member_required
def admin_home(request):
    return redirect('clients')

def chart_context(request, chart):
    rev = chart.revisions.get(revision=chart.revision)
    content = rev.presentation
    result = rev.result
    seconds = round(result['utc_offset'] * 60)
    sign = '+' if seconds >= 0 else '−'
    hours, remainder = divmod(abs(seconds),3600)
    minutes, seconds_part = divmod(remainder,60)
    result = {**result,'utc_offset_label':f'{sign}{hours:02}:{minutes:02}'+(f':{seconds_part:02}' if seconds_part else '')}
    public_content = {key:content[key] for key in ('rows','aspects','uncertainty_rows','variable_aspects','warnings','asc_text')}
    return {**public_content,'chart':chart,'birth':rev.input,'result':result,'client_language':rev.language,'payload':{'result':result,'rows':content['rows'],'signs':content['signs'],'aspects':content['aspects'],'labels':content['t']},'source_url':settings.SOURCE_URL,'contact_text':settings.CONTACT_TEXT}

@require_GET
def public_chart(request, token):
    chart = get_object_or_404(Chart, public_token=token, is_active=True)
    revision = chart.revisions.get(revision=chart.revision)
    with translation.override(revision.language):
        response = render(request, 'chart.html', {**chart_context(request, chart), 'lang':revision.language, 't':revision.presentation['t'], 'hide_language_switch':True})
    response['Content-Language'] = revision.language
    return response

def staff_permission(request, write=False):
    permission = 'charts.change_chart' if write else 'charts.view_chart'
    if not request.user.has_perm(permission):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

@staff_member_required
def clients(request):
    staff_permission(request)
    qs = Chart.objects.select_related('client').filter(revisions__revision=F('revision'))
    q = request.POST.get('q', '').strip() if request.method == 'POST' else ''
    if q:
        if '/c/' in q:
            qs = qs.filter(public_token=urlsplit(q).path.rstrip('/').split('/')[-1])
        else:
            normalized = normalize(q)
            filters = Q(client__search_name__contains=normalized) | Q(search_name__contains=normalized) | Q(revisions__place_search__contains=normalized) | Q(revisions__input__date=q)
            try:
                filters |= Q(pk=uuid.UUID(q)) | Q(client_id=uuid.UUID(q))
            except ValueError:
                pass
            qs = qs.filter(filters).distinct()
    active = request.POST.get('active', '') if request.method == 'POST' else ''
    if active in ('1', '0'):
        qs = qs.filter(is_active=active == '1')
    time_filter = request.POST.get('time_filter', '')
    if time_filter in ('exact','approximate','unknown'):
        qs = qs.filter(revisions__input__time_mode=time_filter)
    created_after = request.POST.get('created_after', '')
    if created_after:
        from datetime import date
        try:
            date.fromisoformat(created_after)
            qs = qs.filter(created_at__date__gte=created_after)
        except ValueError:
            created_after = ''
    order = request.POST.get('order', '-updated_at')
    if order not in ('client__internal_name','created_at','-created_at','updated_at','-updated_at'):
        order = '-updated_at'
    qs = qs.order_by(order)
    page = Paginator(qs, 25).get_page(request.POST.get('page', 1))
    entries = [(c, c.revisions.get(revision=c.revision).input) for c in page]
    return render(request, 'staff/list.html', {'page': page, 'entries': entries, 'q': q, 'active_filter': active, 'time_filter': time_filter, 'created_after': created_after, 'order': order})

@staff_member_required
def editor(request, chart_id=None):
    staff_permission(request, True)
    if not chart_id and not all(request.user.has_perm(p) for p in ('charts.add_chart','charts.add_client')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if chart_id and not request.user.has_perm('charts.change_client'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    chart = get_object_or_404(Chart.objects.select_related('client'), pk=chart_id) if chart_id else None
    initial = {'reason': 'Initial creation'}
    if chart:
        initial = {**chart.revisions.get(revision=chart.revision).input, 'revision': chart.revision, 'internal_name': chart.client.internal_name, 'internal_notes': chart.client.internal_notes, 'display_name': chart.display_name, 'language':chart.language, 'reason': ''}
    form = ChartForm(request.POST or None, initial=initial)
    lang = getattr(request, 'LANGUAGE_CODE', 'uk')[:2]
    for name, field in form.fields.items():
        field.label = WORDS.get(lang, WORDS['uk']).get(name, field.label)
    language = lang if lang in WORDS else 'uk'
    form.fields['language'].label = {'en':'Client chart language','uk':'Мова карти клієнта','ru':'Язык карты клиента'}[language]
    form.fields['language'].help_text = {'en':'The client sees only this language. Saved explanations are fixed in this revision.','uk':'Клієнт бачить лише цю мову. Готові пояснення зберігаються в цій версії.','ru':'Клиент видит только этот язык. Готовые пояснения сохраняются в этой версии.'}[language]
    form.fields['country'].label = {'en':'Country','uk':'Країна','ru':'Страна'}[language]
    form.fields['internal_notes'].label = WORDS[language]['notes']
    if not chart and request.method != 'POST':
        form.initial['reason'] = {'en':'Initial creation','uk':'Створення карти','ru':'Создание карты'}[language]
    first, second = {'en':('First occurrence','Second occurrence'),'uk':('Перший випадок','Другий випадок'),'ru':('Первый случай','Второй случай')}[language]
    form.fields['fold'].choices = [('', '—'), ('0', first), ('1', second)]
    form.fields['time_mode'].choices = {'en':[('exact','Exact'),('approximate','Approximate'),('unknown','Unknown')], 'uk':[('exact','Точний'),('approximate','Приблизний'),('unknown','Невідомий')], 'ru':[('exact','Точное'),('approximate','Приблизительное'),('unknown','Неизвестное')]}[lang if lang in WORDS else 'uk']
    if request.method == 'POST' and form.is_valid():
        try:
            saved = save_chart(form, request.user, chart_id)
            return redirect('client-detail', chart_id=saved.pk)
        except (Conflict, CalculationError, ValueError) as exc:
            form.add_error(None, local_error(str(exc)))
        except DatabaseError:
            form.add_error(None, {'en':'The database could not save this change. The previous chart remains unchanged. Please try again.', 'uk':'База даних не зберегла зміну. Попередня карта залишилася незмінною. Спробуйте ще раз.', 'ru':'База данных не сохранила изменение. Предыдущая карта осталась неизменной. Попробуйте ещё раз.'}[language])
    return render(request, 'staff/editor.html', {'form': form, 'chart': chart})

@staff_member_required
def detail(request, chart_id):
    staff_permission(request)
    chart = get_object_or_404(Chart.objects.select_related('client'), pk=chart_id)
    # Personal URL is fetched only after the explicit copy/open action.
    return render(request, 'staff/detail.html', {**chart_context(request, chart), 'history': chart.revisions.order_by('-revision')})

@staff_member_required
@require_POST
def link(request, chart_id):
    staff_permission(request)
    chart = get_object_or_404(Chart, pk=chart_id)
    return JsonResponse({'url': request.build_absolute_uri(reverse('public-chart', args=[chart.public_token]))})

@staff_member_required
@require_POST
def action(request, chart_id):
    staff_permission(request, True)
    operation = request.POST.get('action')
    if operation not in ('toggle', 'rotate', 'delete') or request.POST.get('confirm') != 'yes':
        return HttpResponse(status=400)
    if operation == 'delete' and not all(request.user.has_perm(p) for p in ('charts.delete_chart','charts.delete_client')):
        return HttpResponse(status=403)
    chart = chart_action(chart_id, operation, request.user)
    return redirect('client-detail', chart_id=chart.pk) if chart else redirect('clients')

@staff_member_required
def places(request):
    staff_permission(request, True)
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    cities = City.objects.filter(search_text__contains=normalize(q))
    if request.GET.get('country'):
        cities = cities.filter(country=request.GET['country'].upper())
    return JsonResponse({'results': [{'id': c.pk, 'label': str(c), 'latitude': c.latitude, 'longitude': c.longitude, 'timezone': c.timezone_id} for c in cities.order_by('name')[:20]]})

def live(request):
    return HttpResponse('ok', content_type='text/plain')

def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        verify_files(settings.EPHEMERIS_PATH)
    except Exception:
        return HttpResponse('unavailable', status=503, content_type='text/plain')
    return live(request)

def robots(request):
    return HttpResponse('User-agent: *\nDisallow: /c/\nDisallow: /admin/\n', content_type='text/plain')
