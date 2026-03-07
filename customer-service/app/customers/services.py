import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

CART_SERVICE_URL = getattr(settings, 'CART_SERVICE_URL', 'http://cart-service:8000')


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
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return {'success': True}
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
