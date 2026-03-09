import logging
import threading
import time
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

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
_pay_cb  = CircuitBreaker(name='pay-service')
_ship_cb = CircuitBreaker(name='ship-service')

# ---------------------------------------------------------------------------


def _request_json(method: str, url: str, **kwargs) -> Dict[str, Any]:
    try:
        resp = requests.request(method, url, timeout=5, **kwargs)
        resp.raise_for_status()
        return {'success': True, 'data': resp.json()}
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code
        detail = exc.response.text
        logger.warning('HTTP %s calling %s %s: %s', status_code, method, url, detail)
        return {'success': False, 'status_code': status_code, 'error': detail}
    except requests.exceptions.RequestException as exc:
        logger.warning('Request error calling %s %s: %s', method, url, exc)
        return {'success': False, 'error': str(exc)}


def fetch_cart_for_order(customer_id: int) -> Dict[str, Any]:
    url = f"{settings.CART_SERVICE_URL}/internal/carts/customer/{customer_id}/for-order/"
    try:
        return _cart_cb.call(_request_json, 'GET', url)
    except CircuitBreakerOpenError:
        logger.warning('cart-service circuit breaker is OPEN for customer_id=%s', customer_id)
        return {'success': False, 'error': 'cart-service circuit open'}


def clear_cart(customer_id: int) -> Dict[str, Any]:
    url = f"{settings.CART_SERVICE_URL}/api/carts/customer/{customer_id}/clear/"
    try:
        return _cart_cb.call(_request_json, 'DELETE', url)
    except CircuitBreakerOpenError:
        logger.warning('cart-service circuit breaker is OPEN for customer_id=%s', customer_id)
        return {'success': False, 'error': 'cart-service circuit open'}


def create_payment(order_id: int, customer_id: int, method: str, amount: str) -> Dict[str, Any]:
    url = f"{settings.PAY_SERVICE_URL}/internal/payments/"
    payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "method": method,
        "amount": str(amount),
    }
    try:
        return _pay_cb.call(_request_json, 'POST', url, json=payload)
    except CircuitBreakerOpenError:
        logger.warning('pay-service circuit breaker is OPEN for order_id=%s', order_id)
        return {'success': False, 'error': 'pay-service circuit open'}


def cancel_payment(payment_id: int) -> Dict[str, Any]:
    url = f"{settings.PAY_SERVICE_URL}/internal/payments/{payment_id}/"
    try:
        return _pay_cb.call(_request_json, 'DELETE', url)
    except CircuitBreakerOpenError:
        logger.warning('pay-service circuit breaker is OPEN for payment_id=%s', payment_id)
        return {'success': False, 'error': 'pay-service circuit open'}


def cancel_shipment(shipment_id: int) -> Dict[str, Any]:
    url = f"{settings.SHIP_SERVICE_URL}/internal/shipments/{shipment_id}/"
    try:
        return _ship_cb.call(_request_json, 'DELETE', url)
    except CircuitBreakerOpenError:
        logger.warning('ship-service circuit breaker is OPEN for shipment_id=%s', shipment_id)
        return {'success': False, 'error': 'ship-service circuit open'}


def create_shipment(order_id: int, customer_id: int, shipping_method: str, shipping_address: str, shipping_fee: str) -> Dict[str, Any]:
    url = f"{settings.SHIP_SERVICE_URL}/internal/shipments/"
    payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "shipping_method": shipping_method,
        "shipping_address": shipping_address,
        "shipping_fee": str(shipping_fee),
    }
    try:
        return _ship_cb.call(_request_json, 'POST', url, json=payload)
    except CircuitBreakerOpenError:
        logger.warning('ship-service circuit breaker is OPEN for order_id=%s', order_id)
        return {'success': False, 'error': 'ship-service circuit open'}
