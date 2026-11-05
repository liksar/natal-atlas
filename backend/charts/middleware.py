import hashlib
import os
import time
import ipaddress
from django.utils import translation
from django.db import transaction
from django.http import HttpResponse
from .models import RateBucket

def allowed(key, limit, seconds=60):
    key = hashlib.sha256(key.encode()).hexdigest()
    window = int(time.time()) // seconds
    with transaction.atomic():
        RateBucket.objects.get_or_create(key=key, defaults={'window': window, 'count': 0})
        bucket = RateBucket.objects.select_for_update().get(key=key)
        bucket.count = bucket.count + 1 if bucket.window == window else 1
        bucket.window = window
        bucket.save()
        return bucket.count <= limit

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        language = request.GET.get('lang') if not request.path.startswith('/c/') else None
        if language in ('en', 'uk', 'ru'):
            translation.activate(language)
            request.LANGUAGE_CODE = language
        scope = None
        remote = request.META.get('REMOTE_ADDR', '')
        trusted = os.getenv('TRUSTED_PROXY_IPS', '').split(',')
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if remote in trusted:
            try:
                remote = str(ipaddress.ip_address(forwarded))
            except ValueError:
                pass
        if request.path.startswith('/c/'):
            scope, limit = 'view', int(os.getenv('RATE_LIMIT_PUBLIC', '120'))
        elif request.path == '/admin/login/' and request.method == 'POST':
            scope, limit = 'login', int(os.getenv('RATE_LIMIT_LOGIN', '8'))
        elif request.path.startswith('/admin/clients/') and request.method == 'POST':
            scope, limit = 'admin', int(os.getenv('RATE_LIMIT_ADMIN', '30'))
        if scope and not allowed(scope + remote, limit):
            return HttpResponse('Too many requests. Please try later.', status=429, headers={'Retry-After': '60'})
        response = self.get_response(request)
        if language in ('en', 'uk', 'ru'):
            response.set_cookie('django_language', language, max_age=31536000, samesite='Lax')
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.path.startswith(('/c/', '/admin/')):
            response['Cache-Control'] = 'private, no-store'
            response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        return response
