import copy
import tempfile
import uuid
import json
from datetime import datetime, timezone
from unittest.mock import patch
import threading
import concurrent.futures
from unittest import skipUnless
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase, TransactionTestCase, Client as Browser, override_settings
from django.db import connection, close_old_connections, connections
from django.urls import reverse
from .engine import calculate, separation, house_of, verify_files, CalculationError
from .timeutils import resolve_time, TimeError
from .forms import ChartForm
from .models import Chart, Client, ChartRevision, City
from .services import save_chart, Conflict, chart_action

def input_data(**kwargs):
    data = {'date': '2000-01-01', 'time': '12:00', 'time_mode': 'exact', 'place': 'Greenwich', 'latitude': 51.4779, 'longitude': 0, 'timezone': 'Etc/UTC', 'fold': None, 'manual_offset': None, 'offset_reason': ''}
    data.update(kwargs)
    return data

def form_data(**kwargs):
    data = {**input_data(), 'key': str(uuid.uuid4()), 'revision': 0, 'internal_name': 'PRIVATE FULL NAME', 'display_name': 'Test atlas', 'language':'uk', 'internal_notes': 'SECRET PRIVATE NOTES', 'reason': 'Test', 'allow_duplicate': True}
    data.update(kwargs)
    return data

class TimeTests(SimpleTestCase):
    def test_dst_gap(self):
        with self.assertRaises(TimeError):
            resolve_time('2024-03-31', '03:30', 'Europe/Kyiv')
    def test_dst_fold(self):
        with self.assertRaises(TimeError):
            resolve_time('2024-10-27', '03:30', 'Europe/Kyiv')
        a = resolve_time('2024-10-27', '03:30', 'Europe/Kyiv', 0)[0]
        b = resolve_time('2024-10-27', '03:30', 'Europe/Kyiv', 1)[0]
        self.assertEqual((b-a).total_seconds(), 3600)
    def test_manual_day_crossing(self):
        utc, offset, source = resolve_time('1950-01-01', '00:30', '', manual_offset=120, comment='Recorded civil offset')
        self.assertEqual(utc.isoformat(), '1949-12-31T22:30:00+00:00')
        self.assertEqual(source, 'manual')
        with self.assertRaises(TimeError):
            resolve_time('1950-01-01', '00:30', '', manual_offset=120)
    def test_historical_offset_seconds_retained(self):
        utc,offset,source=resolve_time('1900-01-01','12:00','Europe/Paris')
        self.assertEqual(offset*60,561)
        self.assertEqual(utc.second,39)
    def test_orb_wrap_and_house_boundary(self):
        self.assertEqual(separation(359, 1), 2)
        cusps = [i*30 for i in range(12)]
        self.assertEqual(house_of(30, cusps), 2)
        self.assertEqual(house_of(359.99, cusps), 12)

class EngineTests(SimpleTestCase):
    def test_independent_jpl_positions(self):
        reference = json.loads((settings.ROOT / 'tests/jpl/reference.json').read_text())
        result = calculate(input_data(date=reference['date']), settings.EPHEMERIS_PATH)
        by_key = {p['key']:p for p in result['planets']}
        for expected in reference['planets']:
            self.assertLess(separation(by_key[expected['key']]['longitude'],expected['longitude']),reference['tolerance_degrees'])
    def test_official_swetest_references(self):
        reference = json.loads((settings.ROOT / 'tests/swetest_reference.json').read_text())
        for case in reference['cases']:
            result = calculate(input_data(date=case['date']), settings.EPHEMERIS_PATH)
            for actual, expected in zip(result['planets'], case['positions'], strict=True):
                self.assertLess(separation(actual['longitude'],expected['longitude']),reference['tolerance_degrees'])
                self.assertLess(abs(actual['speed']-expected['speed']),reference['tolerance_degrees'])
    def test_real_positions(self):
        r = calculate(input_data(), settings.EPHEMERIS_PATH)
        self.assertEqual(len(r['planets']), 11)
        self.assertEqual(len(r['cusps']), 12)
        # J2000 reference: regression only; independent swetest validation is separate.
        self.assertAlmostEqual(r['planets'][0]['longitude'], 280.36891867, places=6)
        self.assertEqual(r['house_system'], 'Placidus')
    def test_unknown(self):
        r = calculate(input_data(time_mode='unknown', time=None), settings.EPHEMERIS_PATH)
        self.assertFalse(r['angles'])
        self.assertFalse(r['cusps'])
        self.assertTrue(all('house' not in p for p in r['planets']))
        self.assertTrue(all('moon' not in (a['a'], a['b']) for a in r['aspects']))
    def test_polar_fallback(self):
        r = calculate(input_data(latitude=80), settings.EPHEMERIS_PATH)
        self.assertEqual(r['house_system'], 'Whole Sign')
        self.assertIn('polar_fallback', r['warnings'])
    def test_approximate(self):
        r = calculate(input_data(time_mode='approximate', uncertainty_minutes=15), settings.EPHEMERIS_PATH)
        self.assertEqual(r['uncertainty']['minutes'], 15)
        self.assertIn('approximate_time', r['warnings'])
    def test_missing_ephemeris(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(CalculationError):
            calculate(input_data(), directory)
    def test_fallback_rejected(self):
        import swisseph as swe
        with patch('charts.engine.swe.calc_ut', return_value=((1,0,0,1,0,0), swe.FLG_MOSEPH, 'fallback')):
            with self.assertRaises(CalculationError):
                calculate(input_data(), settings.EPHEMERIS_PATH)

@override_settings(ALLOWED_HOSTS=['testserver'])
class LifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser('operator', '', 'a-long-test-password')
    def make(self, **kwargs):
        form = ChartForm(form_data(**kwargs))
        self.assertTrue(form.is_valid(), form.errors)
        return save_chart(form, self.user)
    def test_atomic_edit_and_stable_link(self):
        chart = self.make()
        old = chart.public_token
        form = ChartForm(form_data(revision=1, time='15:00'))
        self.assertTrue(form.is_valid(), form.errors)
        saved = save_chart(form, self.user, chart.pk)
        self.assertEqual(saved.public_token, old)
        self.assertEqual(saved.revision, 2)
        self.assertNotEqual(chart.revisions.get(revision=1).result['angles'], saved.revisions.get(revision=2).result['angles'])
        with self.assertRaises(Conflict):
            stale = ChartForm(form_data(revision=1));self.assertTrue(stale.is_valid());save_chart(stale, self.user, chart.pk)
    def test_failed_calculation_rolls_back(self):
        chart = self.make()
        form = ChartForm(form_data(revision=1));self.assertTrue(form.is_valid())
        with patch('charts.services.calculate', side_effect=CalculationError('failed')), self.assertRaises(CalculationError):
            save_chart(form, self.user, chart.pk)
        chart.refresh_from_db()
        self.assertEqual(chart.revision, 1)
        self.assertEqual(chart.revisions.count(), 1)
    def test_failed_creation_leaves_no_client(self):
        form = ChartForm(form_data());self.assertTrue(form.is_valid())
        with patch('charts.services.calculate', side_effect=CalculationError('failed')), self.assertRaises(CalculationError):
            save_chart(form, self.user)
        self.assertEqual(Client.objects.count(), 0)
    def test_idempotency(self):
        form = ChartForm(form_data());self.assertTrue(form.is_valid())
        a = save_chart(form, self.user);b = save_chart(form, self.user)
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(Client.objects.count(), 1)
    def test_public_privacy_and_no_edit(self):
        chart = self.make()
        url = reverse('public-chart', args=[chart.public_token])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'SECRET PRIVATE NOTES')
        self.assertNotContains(response, 'PRIVATE FULL NAME')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertIn('noindex', response['X-Robots-Tag'])
        self.assertEqual(self.client.post(reverse('client-edit', args=[chart.pk]), {k:v for k,v in form_data().items() if v is not None}).status_code, 302)
        self.assertEqual(self.client.get('/admin/places/?q=Ky').status_code, 302)
    def test_xss(self):
        chart = self.make(display_name='<script>alert(1)</script>')
        response = self.client.get(reverse('public-chart', args=[chart.public_token]))
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')
    def test_revocation_rotation(self):
        chart = self.make();old=chart.public_token
        chart_action(chart.pk, 'toggle', self.user)
        self.assertEqual(self.client.get(f'/c/{old}/').status_code,404)
        chart_action(chart.pk, 'toggle', self.user)
        new=chart_action(chart.pk, 'rotate', self.user)
        self.assertEqual(self.client.get(f'/c/{old}/').status_code,404)
        self.assertEqual(self.client.get(f'/c/{new.public_token}/').status_code,200)
    def test_csrf(self):
        browser=Browser(enforce_csrf_checks=True);browser.force_login(self.user)
        self.assertEqual(browser.post('/admin/clients/new/',{k:v for k,v in form_data().items() if v is not None}).status_code,403)
    def test_client_language_is_fixed(self):
        for language, expected in [('en','Planetary positions'),('uk','Положення планет'),('ru','Положения планет')]:
            chart=self.make(language=language)
            self.client.cookies['django_language']='en' if language!='en' else 'ru'
            response=self.client.get(f'/c/{chart.public_token}/?lang=ru',HTTP_ACCEPT_LANGUAGE='ru')
            self.assertContains(response,expected)
            self.assertContains(response,f'<html lang="{language}">')
            self.assertNotContains(response,'id="language"')
            self.assertEqual(response['Content-Language'],language)
            self.assertNotIn('django_language',response.cookies)

    def test_saved_text_is_not_rebuilt(self):
        chart=self.make(language='en')
        before=self.client.get(f'/c/{chart.public_token}/').content
        with patch('charts.presentation.interpretation',side_effect=AssertionError('must not regenerate saved text')):
            after=self.client.get(f'/c/{chart.public_token}/').content
        self.assertEqual(before,after)

    def test_language_edit_keeps_link_and_history(self):
        chart=self.make(language='en')
        old_token=chart.public_token
        old_text=chart.revisions.get(revision=1).presentation
        form=ChartForm(form_data(language='ru',revision=1))
        self.assertTrue(form.is_valid(),form.errors)
        save_chart(form,self.user,chart.pk)
        chart.refresh_from_db()
        self.assertEqual(chart.language,'ru')
        self.assertEqual(chart.public_token,old_token)
        self.assertEqual(chart.revisions.get(revision=1).presentation,old_text)
        self.assertContains(self.client.get(f'/c/{old_token}/'),'Положения планет')
        self.client.force_login(self.user)
        self.client.cookies['django_language']='uk'
        response=self.client.get(f'/admin/clients/{chart.pk}/edit/')
        self.assertContains(response,'Мова карти клієнта')
        self.assertContains(response,'id="language"')
        self.assertContains(response,'value="ru" selected')

    def test_staff_workflow_pages(self):
        chart=self.make();self.client.force_login(self.user)
        for url in ['/admin/clients/','/admin/clients/new/',f'/admin/clients/{chart.pk}/',f'/admin/clients/{chart.pk}/edit/']:
            self.assertEqual(self.client.get(url).status_code,200,url)
        response=self.client.post(reverse('client-link',args=[chart.pk]))
        self.assertIn(chart.public_token,response.json()['url'])

    def test_rate_limit(self):
        chart = self.make()
        with patch.dict('os.environ', {'RATE_LIMIT_PUBLIC':'2'}):
            self.assertEqual(self.client.get(f'/c/{chart.public_token}/').status_code,200)
            self.assertEqual(self.client.get(f'/c/{chart.public_token}/').status_code,200)
            self.assertEqual(self.client.get(f'/c/{chart.public_token}/').status_code,429)

    def test_create_edit_via_http(self):
        self.client.force_login(self.user)
        data={k:v for k,v in form_data().items() if v is not None}
        response=self.client.post('/admin/clients/new/',data)
        self.assertEqual(response.status_code,302)
        chart=Chart.objects.get()
        data.update(key=str(uuid.uuid4()),revision=1,time='18:00')
        response=self.client.post(reverse('client-edit',args=[chart.pk]),data)
        self.assertEqual(response.status_code,302)
        chart.refresh_from_db();self.assertEqual(chart.revision,2)
        url=self.client.post(reverse('client-link',args=[chart.pk])).json()['url']
        self.assertContains(self.client.post('/admin/clients/',{'q':url}),'PRIVATE FULL NAME')

    def test_password_reset_revokes_session(self):
        self.client.force_login(self.user)
        self.user.set_password('a-new-test-password');self.user.save()
        self.assertEqual(self.client.get('/admin/clients/').status_code,302)

    def test_unicode_city_search(self):
        City.objects.create(source_id='test-kyiv',name='Київ',aliases='Kyiv,Киев',country='UA',region='Kyiv',latitude=50.45,longitude=30.52,timezone_id='Europe/Kyiv',dataset_version='test')
        self.client.force_login(self.user)
        for query in ['київ','КИЇВ','KyIv','КИЕВ']:
            response=self.client.get('/admin/places/',{'q':query})
            self.assertEqual(len(response.json()['results']),1,query)

    def test_unicode_client_search(self):
        self.make(internal_name='Олександра',place='Київ')
        self.client.force_login(self.user)
        for query in ['олександра','ОЛЕКСАНДРА','КИЇВ']:
            self.assertContains(self.client.post('/admin/clients/',{'q':query}),'Олександра')

    def test_admin_landing_opens_client_workflow(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get('/admin/'),'/admin/clients/')
        self.assertRedirects(self.client.get('/'),'/admin/clients/')
        self.assertEqual(self.client.get('/admin/system/').status_code,200)

    def test_admin_form_translations_include_country_names(self):
        self.client.force_login(self.user)
        for language, notes, country, reason in [('uk','Внутрішні нотатки','Україна','Створення карти'),('ru','Внутренние заметки','Украина','Создание карты'),('en','Private notes','Ukraine','Initial creation')]:
            self.client.cookies['django_language']=language
            response=self.client.get('/admin/clients/new/')
            for text in (notes,country,reason):
                self.assertContains(response,text)
        response=self.client.get('/admin/clients/')
        self.assertNotContains(response,'вЂ')

@skipUnless(connection.vendor == 'postgresql','Requires PostgreSQL row locks')
class ConcurrencyTests(TransactionTestCase):
    def test_two_edits_only_one_wins(self):
        user=get_user_model().objects.create_superuser('concurrent','','a-test-password')
        form=ChartForm(form_data());self.assertTrue(form.is_valid());chart=save_chart(form,user)
        barrier=threading.Barrier(2)
        real_calculate=calculate
        def synchronised(*args,**kwargs):
            result=real_calculate(*args,**kwargs)
            barrier.wait(timeout=20)
            return result
        def edit(clock):
            close_old_connections()
            try:
                actor=get_user_model().objects.get(pk=user.pk)
                edit_form=ChartForm(form_data(revision=1,time=clock))
                assert edit_form.is_valid(),edit_form.errors
                try:
                    save_chart(edit_form,actor,chart.pk)
                    return 'saved'
                except Conflict:
                    return 'conflict'
            finally:
                connections.close_all()
        with patch('charts.services.calculate',side_effect=synchronised), concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(edit,['14:00','16:00']))
        self.assertCountEqual(results,['saved','conflict'])
        chart.refresh_from_db();self.assertEqual(chart.revision,2)
        self.assertEqual(chart.revisions.count(),2)
