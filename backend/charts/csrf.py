from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class LocalPreviewCsrfMiddleware(CsrfViewMiddleware):
    """Permit opaque-origin previews only on the opted-in loopback dev server.

    Django's cookie/token checks still run unchanged. Never trust null origins
    on a deployed host, even if someone accidentally exports the preview flag.
    """
    def _origin_verified(self, request):
        if (
            settings.DEBUG
            and settings.LOCAL_PREVIEW_NULL_ORIGIN
            and request.META.get('HTTP_ORIGIN') == 'null'
            and request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1')
            and request.get_host().split(':')[0] in ('127.0.0.1', 'localhost')
        ):
            return True
        return super()._origin_verified(request)
