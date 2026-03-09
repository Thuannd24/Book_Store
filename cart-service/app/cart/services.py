import logging
import threading
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BOOK_SERVICE_URL = getattr(settings, 'BOOK_SERVICE_URL', 'http://book-service:8000')

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


_book_cb = CircuitBreaker(name='book-service')

# ---------------------------------------------------------------------------


def get_book_detail(book_id: int) -> dict:
    """
    Call book-service internal endpoint to validate book and retrieve snapshot data.

    Fixed contract (book-service frozen):
        GET /internal/books/{book_id}/
        200 -> {
            "success": true,
            "book": {
                "id": 5,
                "title": "Clean Code",
                "price": "120.00",
                "stock": 10,
                "status": "ACTIVE",
                "category_id": 2,
                "category_name_snapshot": "Software Engineering"
            }
        }

    Returns:
        {'success': True, 'book': {...}} on success
        {'success': False, 'error': '...'} on any failure
    """
    url = f'{BOOK_SERVICE_URL}/internal/books/{book_id}/'
    try:
        response = _book_cb.call(requests.get, url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data.get('success'):
            return {'success': False, 'error': 'book-service returned success=false'}
        return {'success': True, 'book': data['book']}
    except CircuitBreakerOpenError:
        logger.warning('book-service circuit breaker is OPEN for book_id=%s', book_id)
        return {'success': False, 'error': 'book-service circuit open'}
    except requests.exceptions.ConnectionError as exc:
        logger.warning('book-service unreachable: %s', exc)
        return {'success': False, 'error': 'book-service is unreachable'}
    except requests.exceptions.Timeout:
        logger.warning('book-service timed out for book_id=%s', book_id)
        return {'success': False, 'error': 'book-service timed out'}
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code
        logger.warning('book-service returned HTTP %s for book_id=%s', status_code, book_id)
        if status_code == 404:
            return {'success': False, 'error': f'Book {book_id} not found'}
        return {'success': False, 'error': f'book-service error: HTTP {status_code}'}
    except Exception as exc:  # noqa: BLE001
        logger.exception('Unexpected error calling book-service: %s', exc)
        return {'success': False, 'error': str(exc)}
