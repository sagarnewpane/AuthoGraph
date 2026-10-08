"""Accept client IP metadata only when signed by the trusted frontend server."""
import hashlib
import hmac
import ipaddress
import time
from django.conf import settings


class TrustedClientIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.headers.get('X-Authograph-IP', '')
        timestamp = request.headers.get('X-Authograph-Time', '')
        signature = request.headers.get('X-Authograph-Signature', '')
        if settings.INTERNAL_PROXY_SECRET and ip and timestamp and signature:
            try:
                ipaddress.ip_address(ip)
                recent = abs(time.time() - int(timestamp)) < 60
                expected = hmac.new(settings.INTERNAL_PROXY_SECRET.encode(), f'{timestamp}:{ip}'.encode(), hashlib.sha256).hexdigest()
                if recent and hmac.compare_digest(expected, signature):
                    request.META['REMOTE_ADDR'] = ip
            except ValueError:
                pass
        # DRF must not trust arbitrary forwarded headers independently of our signature.
        request.META.pop('HTTP_X_FORWARDED_FOR', None)
        return self.get_response(request)
