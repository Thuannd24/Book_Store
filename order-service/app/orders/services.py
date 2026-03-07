import logging
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


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
    return _request_json('GET', url)


def clear_cart(customer_id: int) -> Dict[str, Any]:
    url = f"{settings.CART_SERVICE_URL}/api/carts/customer/{customer_id}/clear/"
    return _request_json('DELETE', url)


def create_payment(order_id: int, customer_id: int, method: str, amount: str) -> Dict[str, Any]:
    url = f"{settings.PAY_SERVICE_URL}/internal/payments/"
    payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "method": method,
        "amount": str(amount),
    }
    return _request_json('POST', url, json=payload)


def create_shipment(order_id: int, customer_id: int, shipping_method: str, shipping_address: str, shipping_fee: str) -> Dict[str, Any]:
    url = f"{settings.SHIP_SERVICE_URL}/internal/shipments/"
    payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "shipping_method": shipping_method,
        "shipping_address": shipping_address,
        "shipping_fee": str(shipping_fee),
    }
    return _request_json('POST', url, json=payload)
