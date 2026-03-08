import json
import logging
from typing import Any, Dict, List

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


def _rule_based_fallback(
    purchased_ids: set,
    books: List[Dict[str, Any]],
    rating_map: Dict[int, float],
    book_map: Dict[int, Dict[str, Any]],
    top_n: int,
) -> List[Dict[str, Any]]:
    """Original rule-based scoring used as fallback when Gemini is unavailable."""
    from collections import Counter

    category_counter = Counter()
    for book_id in purchased_ids:
        book = book_map.get(book_id)
        if book:
            category_counter[book.get('category_id')] += 1
    preferred_categories = [cat for cat, _ in category_counter.most_common()]

    candidates = []
    for book in books:
        book_id = book.get('id')
        if not book_id or book_id in purchased_ids:
            continue
        if book.get('status') != 'ACTIVE' or int(book.get('stock', 0) or 0) <= 0:
            continue

        category_id = book.get('category_id')
        avg_rating = rating_map.get(book_id, 0.0)
        stock = int(book.get('stock', 0) or 0)

        score = 0.0
        reasons = []

        if preferred_categories:
            if category_id in preferred_categories:
                score += 5.0
                reasons.append("same category")
        else:
            score += 1.0

        score += avg_rating
        if avg_rating >= 4.0:
            reasons.append("high rating")

        score += min(stock, 50) * 0.02
        if stock > 0:
            reasons.append("in stock")

        reason_text = " and ".join(reasons) if reasons else "recommended"

        candidates.append((
            score,
            {
                'book_id': book_id,
                'title': book.get('title'),
                'score': round(score, 2),
                'reason': reason_text,
                'average_rating': round(avg_rating, 2),
                'category_id': category_id,
            }
        ))

    candidates.sort(key=lambda item: (
        -item[0],
        -rating_map.get(item[1]['book_id'], 0.0),
        -int(book_map[item[1]['book_id']].get('stock', 0) or 0),
        item[1]['book_id'],
    ))
    return [payload for _, payload in candidates[:top_n]]


def _recommend_with_gemini(
    purchased_books_info: List[Dict[str, Any]],
    candidate_books: List[Dict[str, Any]],
    rating_map: Dict[int, float],
    top_n: int,
) -> List[Dict[str, Any]]:
    """Call Google Gemini gemini-2.0-flash to select and explain recommendations."""
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Build purchase history summary
    if purchased_books_info:
        history_lines = [
            f"- \"{b.get('title', 'Unknown')}\" (category_id: {b.get('category_id', 'N/A')}, author: {b.get('author', 'N/A')})"
            for b in purchased_books_info
        ]
        history_text = "\n".join(history_lines)
    else:
        history_text = "No purchase history (new customer)."

    # Build candidate list
    candidate_lines = []
    for b in candidate_books:
        book_id = b.get('id')
        avg_rating = rating_map.get(book_id, 0.0)
        candidate_lines.append(
            f"- id={book_id}, title=\"{b.get('title', '')}\", author=\"{b.get('author', '')}\", "
            f"category_id={b.get('category_id')}, average_rating={avg_rating:.1f}, stock={b.get('stock', 0)}"
        )
    candidates_text = "\n".join(candidate_lines)

    prompt = f"""You are a book recommendation engine for an online bookstore.

Customer purchase history:
{history_text}

Available books to recommend (not yet purchased, in stock, active):
{candidates_text}

Task: Select the top {top_n} books to recommend to this customer. Base your selection on:
- Relevance to their reading preferences and past purchases
- High ratings
- Good availability (stock)
- Variety (don't recommend all books from the same category unless the customer strongly prefers it)

Respond ONLY with a valid JSON array (no markdown, no explanation outside JSON) in this exact format:
[
  {{"book_id": <int>, "reason": "<short English explanation why this book is recommended>"}},
  ...
]
"""

    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    gemini_picks = json.loads(raw)

    # Build final result enriched with book data
    result = []
    candidate_map = {b['id']: b for b in candidate_books if 'id' in b}
    for pick in gemini_picks[:top_n]:
        book_id = pick.get('book_id')
        book = candidate_map.get(book_id)
        if not book:
            continue
        avg_rating = rating_map.get(book_id, 0.0)
        result.append({
            'book_id': book_id,
            'title': book.get('title'),
            'score': None,  # Gemini-based; no numeric score
            'reason': pick.get('reason', 'Recommended by AI'),
            'average_rating': round(avg_rating, 2),
            'category_id': book.get('category_id'),
        })

    return result


def compute_recommendations(customer_id: int, top_n: int = TOP_N) -> List[Dict[str, Any]]:
    history = fetch_purchase_history(customer_id)
    books = fetch_books()
    ratings = fetch_ratings()

    purchased_ids = {item['book_id'] for item in history.get('books', []) if 'book_id' in item}

    book_map: Dict[int, Dict[str, Any]] = {book['id']: book for book in books if 'id' in book}
    rating_map: Dict[int, float] = {
        item['book_id']: float(item.get('average_rating') or 0)
        for item in ratings if 'book_id' in item
    }

    # Filter candidates: ACTIVE, in stock, not yet purchased
    candidate_books = [
        book for book in books
        if book.get('id')
        and book.get('id') not in purchased_ids
        and book.get('status') == 'ACTIVE'
        and int(book.get('stock', 0) or 0) > 0
    ]

    # Purchased books info for context
    purchased_books_info = [book_map[bid] for bid in purchased_ids if bid in book_map]

    # Try Gemini first; fall back to rule-based on any error
    gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
    if gemini_key and candidate_books:
        try:
            return _recommend_with_gemini(
                purchased_books_info=purchased_books_info,
                candidate_books=candidate_books,
                rating_map=rating_map,
                top_n=top_n,
            )
        except Exception as exc:
            logger.warning("Gemini recommendation failed, falling back to rule-based: %s", exc)

    # Fallback
    return _rule_based_fallback(
        purchased_ids=purchased_ids,
        books=books,
        rating_map=rating_map,
        book_map=book_map,
        top_n=top_n,
    )
