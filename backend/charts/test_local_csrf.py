from django.test import TestCase, Client, override_settings


@override_settings(DEBUG=True, LOCAL_PREVIEW_NULL_ORIGIN=True, ALLOWED_HOSTS=['127.0.0.1','atlas.example.com'])
class LocalCsrfTests(TestCase):
    def browser(self):
        browser=Client(enforce_csrf_checks=True)
        browser.get('/admin/login/',HTTP_HOST='127.0.0.1:8000')
        return browser

    def test_null_origin_with_token_passes_csrf(self):
        browser=self.browser()
        response=browser.post('/admin/login/',{'username':'nonexistent','password':'wrong','csrfmiddlewaretoken':browser.cookies['csrftoken'].value},HTTP_HOST='127.0.0.1:8000',HTTP_ORIGIN='null')
        self.assertEqual(response.status_code,200)

    def test_null_origin_without_token_is_rejected(self):
        browser=self.browser()
        self.assertEqual(browser.post('/admin/login/',{},HTTP_HOST='127.0.0.1:8000',HTTP_ORIGIN='null').status_code,403)

    def test_deployed_host_is_rejected(self):
        browser=self.browser()
        token=browser.cookies['csrftoken'].value
        response=browser.post('/admin/login/',{'csrfmiddlewaretoken':token},HTTP_HOST='atlas.example.com',HTTP_ORIGIN='null')
        self.assertEqual(response.status_code,403)

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_production_mode_is_rejected(self):
        browser=self.browser()
        response=browser.post('/admin/login/',{'csrfmiddlewaretoken':browser.cookies['csrftoken'].value},HTTP_HOST='127.0.0.1:8000',HTTP_ORIGIN='null')
        self.assertEqual(response.status_code,403)

    def test_external_remote_address_is_rejected(self):
        browser=self.browser()
        response=browser.post('/admin/login/',{'csrfmiddlewaretoken':browser.cookies['csrftoken'].value},HTTP_HOST='127.0.0.1:8000',HTTP_ORIGIN='null',REMOTE_ADDR='192.0.2.5')
        self.assertEqual(response.status_code,403)
