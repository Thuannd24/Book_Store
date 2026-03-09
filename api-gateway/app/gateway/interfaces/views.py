import logging
import threading
import time

import requests
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

_START_TIME = time.time()

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

# ---------------------------------------------------------------------------


@api_view(['GET'])
def health(request):
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False
    return Response({
        'status': 'ok' if db_ok else 'degraded',
        'service': 'api-gateway',
        'db': 'ok' if db_ok else 'error',
        'version': '2.0.0',
    }, status=200 if db_ok else 503)


@api_view(['GET'])
def metrics(request):
    return Response({
        'uptime_seconds': round(time.time() - _START_TIME, 2),
        'service': 'api-gateway',
        'version': '2.0.0',
    })


SERVICE_MAP = {
    'customers': settings.CUSTOMER_SERVICE_URL,
    'books': settings.BOOK_SERVICE_URL,
    'carts': settings.CART_SERVICE_URL,
    'orders': settings.ORDER_SERVICE_URL,
    'reviews': settings.REVIEW_SERVICE_URL,
    'recommendations': settings.RECOMMENDER_SERVICE_URL,
    'catalog': settings.CATALOG_SERVICE_URL,
    'staff': settings.STAFF_SERVICE_URL,
    'managers': settings.MANAGER_SERVICE_URL,
}

_circuit_breakers = {key: CircuitBreaker(name=key) for key in SERVICE_MAP}


@api_view(['GET'])
def circuit_breaker_status(request):
    return Response({
        name: cb.state
        for name, cb in _circuit_breakers.items()
    })


class ProxyView(APIView):
    """
    Proxies any method to the mapped downstream service.
    """

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def _proxy(self, request, service_key, path_suffix):
        base_url = SERVICE_MAP.get(service_key)
        if not base_url:
            return Response({'detail': 'Unknown service'}, status=status.HTTP_400_BAD_REQUEST)

        target_url = f"{base_url.rstrip('/')}/{path_suffix}"

        try:
            # Build forward headers: include auth, content-type, and JWT user context
            forward_headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() in ('authorization', 'content-type')
            }
            user_id = getattr(request, 'jwt_user_id', None)
            role = getattr(request, 'jwt_role', None)
            if user_id is not None:
                forward_headers['X-User-Id'] = str(user_id)
            if role is not None:
                forward_headers['X-User-Role'] = role

            cb = _circuit_breakers.get(service_key)
            if cb is None:
                return Response({'detail': 'Unknown service'}, status=status.HTTP_400_BAD_REQUEST)

            resp = cb.call(
                requests.request,
                method=request.method,
                url=target_url,
                params=request.GET,
                json=request.data if request.body else None,
                headers=forward_headers,
                timeout=10,
            )
        except CircuitBreakerOpenError:
            logger.warning('Circuit breaker OPEN for service_key=%s', service_key)
            return Response(
                {'detail': f'{service_key} is temporarily unavailable (circuit open).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except requests.RequestException as exc:
            logger.warning("Proxy error to %s: %s", target_url, exc)
            return Response({'detail': 'Upstream unavailable', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Unexpected proxy error to %s: %s", target_url, exc)
            return Response({'detail': 'Upstream unavailable', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = resp.json()
            return Response(data, status=resp.status_code)

        return HttpResponse(resp.content, status=resp.status_code, content_type=content_type or 'application/octet-stream')

    def get(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def post(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def put(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def patch(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def delete(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)


class AuthProxyView(APIView):
    """
    Proxies all requests to the auth-service.
    Route: /api/gateway/auth/<path_suffix>
    """

    def _proxy_auth(self, request, path_suffix):
        auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://auth-service:8000')
        target_url = f"{auth_service_url.rstrip('/')}/auth/{path_suffix}"

        try:
            resp = requests.request(
                method=request.method,
                url=target_url,
                params=request.GET,
                json=request.data if request.body else None,
                headers={
                    key: value
                    for key, value in request.headers.items()
                    if key.lower() in ('authorization', 'content-type')
                },
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.warning('Auth proxy error to %s: %s', target_url, exc)
            return Response({'detail': 'Auth service unavailable', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return Response(resp.json(), status=resp.status_code)
        return HttpResponse(resp.content, status=resp.status_code, content_type=content_type or 'application/octet-stream')

    def get(self, request, path_suffix):
        return self._proxy_auth(request, path_suffix)

    def post(self, request, path_suffix):
        return self._proxy_auth(request, path_suffix)

    def put(self, request, path_suffix):
        return self._proxy_auth(request, path_suffix)

    def patch(self, request, path_suffix):
        return self._proxy_auth(request, path_suffix)

    def delete(self, request, path_suffix):
        return self._proxy_auth(request, path_suffix)
