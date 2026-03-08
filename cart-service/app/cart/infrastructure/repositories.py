import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BOOK_SERVICE_URL = getattr(settings, 'BOOK_SERVICE_URL', 'http://book-service:8000')


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
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data.get('success'):
            return {'success': False, 'error': 'book-service returned success=false'}
        return {'success': True, 'book': data['book']}
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
