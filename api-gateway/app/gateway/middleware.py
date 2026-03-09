import json
import logging
import threading
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
import requests

logger = logging.getLogger('gateway')

# ---------------------------------------------------------------------------
# Circuit Breaker (pure-Python, zero external dependencies)
# ---------------------------------------------------------------------------

_cb_logger = logging.getLogger('circuit_breaker')


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is OPEN and the call is rejected."""


class CircuitBreaker:
    """
    Simple in-process Circuit Breaker with CLOSED / OPEN / HALF_OPEN states.

    States:
        CLOSED     – normal operation, failures are counted.
        OPEN       – fast-fail, no calls pass through until recovery_timeout expires.
        HALF_OPEN  – one trial call is allowed; success → CLOSED, failure → OPEN.

    Thread-safe via threading.Lock.
    """

    _STATE_CLOSED    = 'CLOSED'
    _STATE_OPEN      = 'OPEN'
    _STATE_HALF_OPEN = 'HALF_OPEN'

    def __init__(self, name, failure_threshold=3, recovery_timeout=30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout

        self._state          = self._STATE_CLOSED
        self._failure_count  = 0
        self._opened_at      = None
        self._lock           = threading.Lock()

    @property
    def state(self):
        with self._lock:
            return self._get_state_locked()

    def _get_state_locked(self):
        """Must be called with self._lock held."""
        if self._state == self._STATE_OPEN:
            if self._opened_at and (time.monotonic() - self._opened_at) >= self.recovery_timeout:
                self._state = self._STATE_HALF_OPEN
                _cb_logger.info('[CircuitBreaker:%s] OPEN → HALF_OPEN', self.name)
        return self._state

    def call(self, func, *args, **kwargs):
        """Execute func if the circuit allows it; otherwise raise CircuitBreakerOpenError."""
        with self._lock:
            state = self._get_state_locked()
            if state == self._STATE_OPEN:
                raise CircuitBreakerOpenError(
                    f'Circuit breaker [{self.name}] is OPEN – rejecting call'
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == self._STATE_HALF_OPEN:
                _cb_logger.info('[CircuitBreaker:%s] HALF_OPEN → CLOSED', self.name)
            self._state         = self._STATE_CLOSED
            self._failure_count = 0
            self._opened_at     = None

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            _cb_logger.warning(
                '[CircuitBreaker:%s] failure #%d (threshold=%d)',
                self.name, self._failure_count, self.failure_threshold,
            )
            if self._failure_count >= self.failure_threshold or self._state == self._STATE_HALF_OPEN:
                self._state     = self._STATE_OPEN
                self._opened_at = time.monotonic()
                _cb_logger.error(
                    '[CircuitBreaker:%s] OPEN (will retry after %ss)',
                    self.name, self.recovery_timeout,
                )


_auth_cb = CircuitBreaker(name='auth-service', failure_threshold=3, recovery_timeout=30.0)

# ---------------------------------------------------------------------------


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
            resp = _auth_cb.call(
                requests.post,
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
        except CircuitBreakerOpenError:
            logger.warning('auth-service circuit breaker is OPEN')
            return JsonResponse({'detail': 'Authentication service temporarily unavailable.'}, status=503)
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
