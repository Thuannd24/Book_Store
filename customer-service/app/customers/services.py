import logging
import threading
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CART_SERVICE_URL = getattr(settings, 'CART_SERVICE_URL', 'http://cart-service:8000')

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


_cart_cb = CircuitBreaker(name='cart-service')

# ---------------------------------------------------------------------------


def create_cart_for_customer(customer_id: int) -> dict:
    """
    Call cart-service to auto-create an empty cart for a newly registered customer.

    Returns:
        {'success': True}  on success
        {'success': False, 'error': '<reason>'}  on failure

    Business rule: caller must NOT rollback customer creation on failure.
    """
    url = f'{CART_SERVICE_URL}/internal/carts/auto-create/'
    payload = {'customer_id': customer_id}

    try:
        response = _cart_cb.call(requests.post, url, json=payload, timeout=5)
        response.raise_for_status()
        return {'success': True}
    except CircuitBreakerOpenError:
        logger.warning('cart-service circuit breaker is OPEN for customer_id=%s', customer_id)
        return {'success': False, 'error': 'cart-service circuit open'}
    except requests.exceptions.ConnectionError as exc:
        logger.warning('cart-service unreachable: %s', exc)
        return {'success': False, 'error': 'cart-service is unreachable'}
    except requests.exceptions.Timeout:
        logger.warning('cart-service timed out for customer_id=%s', customer_id)
        return {'success': False, 'error': 'cart-service timed out'}
    except requests.exceptions.HTTPError as exc:
        logger.warning('cart-service returned error %s: %s', exc.response.status_code, exc)
        return {'success': False, 'error': f'cart-service error: HTTP {exc.response.status_code}'}
    except Exception as exc:  # noqa: BLE001
        logger.exception('Unexpected error calling cart-service: %s', exc)
        return {'success': False, 'error': str(exc)}
