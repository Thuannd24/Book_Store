import logging
from typing import Any, Callable, Dict, Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5


def _fetch_json(url: str) -> Any:
    response = requests.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _safe_count(fetcher: Callable[[], Any], unavailable_message: str) -> Tuple[Optional[int], Optional[str]]:
    try:
        data = fetcher()
    except requests.RequestException as exc:
        logger.warning("Service call failed: %s", exc)
        return None, f"unreachable: {exc}"
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unexpected error during service call: %s", exc)
        return None, f"error: {exc}"

    if isinstance(data, list):
        return len(data), None
    if isinstance(data, dict):
        if 'count' in data and isinstance(data['count'], int):
            return data['count'], None
        if 'results' in data and isinstance(data['results'], list):
            return len(data['results']), None
    return None, unavailable_message


def get_customers_count() -> Tuple[Optional[int], Optional[str]]:
    url = f"{settings.CUSTOMER_SERVICE_URL.rstrip('/')}/api/customers/"
    return _safe_count(lambda: _fetch_json(url), "customers count endpoint not available")


def get_books_count() -> Tuple[Optional[int], Optional[str]]:
    url = f"{settings.BOOK_SERVICE_URL.rstrip('/')}/api/books/"
    return _safe_count(lambda: _fetch_json(url), "books list endpoint returned unexpected format")


def get_orders_count() -> Tuple[Optional[int], Optional[str]]:
    url = f"{settings.ORDER_SERVICE_URL.rstrip('/')}/api/orders/"
    return _safe_count(lambda: _fetch_json(url), "orders list/count endpoint not available")


def get_reviews_count() -> Tuple[Optional[int], Optional[str]]:
    url = f"{settings.REVIEW_SERVICE_URL.rstrip('/')}/api/reviews/books/summary/averages/"

    try:
        data = _fetch_json(url)
    except requests.RequestException as exc:
        logger.warning("Service call failed: %s", exc)
        return None, f"unreachable: {exc}"
    except Exception as exc:  # pragma: no cover
        logger.warning("Unexpected error during service call: %s", exc)
        return None, f"error: {exc}"

    if isinstance(data, list):
        return sum(int(item.get('review_count', 0)) for item in data), None
    if isinstance(data, dict) and 'review_count' in data and 'book_id' in data:
        return int(data.get('review_count') or 0), None
    return None, "reviews summary endpoint returned unexpected format"


def build_dashboard_summary() -> Dict[str, Any]:
    summary = {}
    notes: Dict[str, str] = {}

    for key, getter in [
        ('total_customers', get_customers_count),
        ('total_books', get_books_count),
        ('total_orders', get_orders_count),
        ('total_reviews', get_reviews_count),
    ]:
        count, note = getter()
        summary[key] = count
        if note:
            notes[key] = note

    if notes:
        summary['notes'] = notes
    return summary
