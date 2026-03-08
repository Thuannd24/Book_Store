import json
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
import requests

logger = logging.getLogger('gateway')


class JWTAuthMiddleware:
    """
    Validates JWT tokens by calling auth-service.
    Skips validation for health, login, register, and auth endpoints.
    """

    SKIP_PATHS = [
        '/api/health/',
        '/api/gateway/customers/register/',
        '/api/gateway/customers/login/',
        '/api/gateway/auth/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'JWT_AUTH_ENABLED', False):
            return self.get_response(request)

        if any(request.path.startswith(p) for p in self.SKIP_PATHS):
            return self.get_response(request)

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        token = auth_header.split(' ', 1)[1]

        auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://auth-service:8000')
        try:
            resp = requests.post(
                f"{auth_service_url}/auth/token/verify/",
                json={'token': token},
                timeout=5,
            )
            if resp.status_code != 200:
                return JsonResponse({'detail': 'Invalid or expired token.'}, status=401)
            token_data = resp.json()
            request.jwt_user_id = token_data.get('user_id')
            request.jwt_role = token_data.get('role')
            request.jwt_email = token_data.get('email')
        except requests.RequestException:
            return JsonResponse({'detail': 'Authentication service unavailable.'}, status=503)

        return self.get_response(request)


class RateLimitMiddleware:
    """
    Simple rate limiting: 100 requests per minute per IP.
    Uses Django cache (Redis or LocMem).
    """

    RATE_LIMIT = 100  # requests
    WINDOW = 60       # seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'RATE_LIMIT_ENABLED', False):
            return self.get_response(request)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown'))
        ip = ip.split(',')[0].strip()
        # Sanitize IP for use as cache key (replace chars not valid in memcache keys)
        safe_ip = ip.replace(':', '_').replace('.', '_')
        cache_key = f'rl:{safe_ip}'

        current = cache.get(cache_key, 0)
        if current >= self.RATE_LIMIT:
            return JsonResponse({'detail': 'Rate limit exceeded. Try again later.'}, status=429)

        cache.set(cache_key, current + 1, timeout=self.WINDOW)
        return self.get_response(request)


class RequestLoggingMiddleware:
    """Structured JSON logging for every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(json.dumps({
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration_ms,
            'ip': request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
            'user_id': getattr(request, 'jwt_user_id', None),
            'role': getattr(request, 'jwt_role', None),
        }))

        return response
