import logging
from collections import Counter
from typing import Any, Dict, List, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5
TOP_N = 5


class ServiceError(Exception):
    """Raised when a downstream service cannot be reached or returns bad data."""


def _fetch_json(url: str) -> Any:
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.warning("Failed calling %s: %s", url, exc)
        raise ServiceError(f"upstream error: {exc}") from exc


def fetch_purchase_history(customer_id: int) -> Dict[str, Any]:
    url = f"{settings.ORDER_SERVICE_URL.rstrip('/')}/internal/orders/customer/{customer_id}/history/"
    data = _fetch_json(url)
    if not isinstance(data, dict) or 'books' not in data:
        raise ServiceError("unexpected purchase history format")
    return data


def fetch_books() -> List[Dict[str, Any]]:
    url = f"{settings.BOOK_SERVICE_URL.rstrip('/')}/api/books/"
    data = _fetch_json(url)
    if not isinstance(data, list):
        raise ServiceError("unexpected books list format")
    return data


def fetch_ratings() -> List[Dict[str, Any]]:
    url = f"{settings.REVIEW_SERVICE_URL.rstrip('/')}/api/reviews/books/summary/averages/"
    data = _fetch_json(url)
    if not isinstance(data, list):
        raise ServiceError("unexpected ratings list format")
    return data


def compute_recommendations(customer_id: int, top_n: int = TOP_N) -> List[Dict[str, Any]]:
    history = fetch_purchase_history(customer_id)
    books = fetch_books()
    ratings = fetch_ratings()

    purchased_ids = {item['book_id'] for item in history.get('books', []) if 'book_id' in item}

    # Map books and ratings for quick lookup
    book_map: Dict[int, Dict[str, Any]] = {book['id']: book for book in books if 'id' in book}
    rating_map: Dict[int, float] = {
        item['book_id']: float(item.get('average_rating') or 0) for item in ratings if 'book_id' in item
    }

    # Preferred categories from purchased books
    category_counter = Counter()
    for book_id in purchased_ids:
        book = book_map.get(book_id)
        if book:
            category_counter[book.get('category_id')] += 1
    preferred_categories = [cat for cat, _ in category_counter.most_common()]

    # Build candidate list
    candidates: List[Tuple[float, Dict[str, Any]]] = []
    for book in books:
        book_id = book.get('id')
        if not book_id or book_id in purchased_ids:
            continue
        status = book.get('status')
        stock = int(book.get('stock', 0) or 0)
        if status != 'ACTIVE' or stock <= 0:
            continue

        category_id = book.get('category_id')
        avg_rating = rating_map.get(book_id, 0.0)

        score = 0.0
        reasons = []

        if preferred_categories:
            if category_id in preferred_categories:
                score += 5.0
                reasons.append("same category")
        else:
            # no history: neutral boost so we still sort by rating/stock
            score += 1.0

        score += avg_rating  # prioritize higher ratings directly
        if avg_rating >= 4.0:
            reasons.append("high rating")

        # slight stock signal (more stock implies availability)
        score += min(stock, 50) * 0.02
        if stock > 0:
            reasons.append("in stock")

        reason_text = " and ".join(reasons) if reasons else "recommended"

        candidates.append(
            (
                score,
                {
                    'book_id': book_id,
                    'title': book.get('title'),
                    'score': round(score, 2),
                    'reason': reason_text,
                    'average_rating': round(avg_rating, 2),
                    'category_id': category_id,
                },
            )
        )

    # Sort by score desc, then rating desc, then stock desc, then id asc
    candidates.sort(
        key=lambda item: (
            -item[0],
            -rating_map.get(item[1]['book_id'], 0.0),
            -int(book_map[item[1]['book_id']].get('stock', 0) or 0),
            item[1]['book_id'],
        )
    )
    top_candidates = [payload for _, payload in candidates[:top_n]]
    return top_candidates
