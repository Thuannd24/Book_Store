from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ReviewSerializer
from comment_rate.infrastructure.mongo import (
    check_mongo_health,
    ensure_indexes,
    get_next_review_id,
    get_reviews_collection,
    now_utc,
)


ACTIVE_STATUS = 'ACTIVE'


def _serialize_review(doc):
    return {
        'id': doc.get('id'),
        'book_id': doc.get('book_id'),
        'customer_id': doc.get('customer_id'),
        'rating': doc.get('rating'),
        'comment': doc.get('comment', ''),
        'status': doc.get('status', ACTIVE_STATUS),
        'created_at': doc.get('created_at'),
    }


@api_view(['GET'])
def health(request):
    ok = check_mongo_health()
    return Response(
        {
            'status': 'ok' if ok else 'degraded',
            'service': 'comment-rate-service',
            'mongo': 'ok' if ok else 'error',
        },
        status=200 if ok else 503,
    )


class ReviewCreateView(APIView):
    """
    POST /api/reviews/
    """

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ensure_indexes()
        data = serializer.validated_data
        review_doc = {
            'id': get_next_review_id(),
            'book_id': data['book_id'],
            'customer_id': data['customer_id'],
            'rating': data['rating'],
            'comment': data.get('comment', ''),
            'status': ACTIVE_STATUS,
            'created_at': now_utc(),
        }
        get_reviews_collection().insert_one(review_doc)

        return Response(ReviewSerializer(_serialize_review(review_doc)).data, status=status.HTTP_201_CREATED)


class ReviewsByBookView(APIView):
    """
    GET /api/reviews/book/{book_id}/
    """

    def get(self, request, book_id):
        ensure_indexes()
        reviews = list(
            get_reviews_collection().find(
                {'book_id': int(book_id), 'status': ACTIVE_STATUS},
                {'_id': 0},
            ).sort('created_at', -1)
        )
        payload = [ReviewSerializer(_serialize_review(doc)).data for doc in reviews]
        return Response(payload)


class ReviewsByCustomerView(APIView):
    """
    GET /api/reviews/customer/{customer_id}/
    """

    def get(self, request, customer_id):
        ensure_indexes()
        reviews = list(
            get_reviews_collection().find(
                {'customer_id': int(customer_id), 'status': ACTIVE_STATUS},
                {'_id': 0},
            ).sort('created_at', -1)
        )
        payload = [ReviewSerializer(_serialize_review(doc)).data for doc in reviews]
        return Response(payload)


class BookAverageView(APIView):
    """
    GET /api/reviews/book/{book_id}/average/
    Returns: {"book_id": X, "average_rating": 4.5, "review_count": 3}
    """

    def get(self, request, book_id):
        ensure_indexes()
        pipeline = [
            {'$match': {'book_id': int(book_id), 'status': ACTIVE_STATUS}},
            {'$group': {'_id': None, 'average_rating': {'$avg': '$rating'}, 'review_count': {'$sum': 1}}},
        ]
        result = list(get_reviews_collection().aggregate(pipeline))
        if not result:
            return Response({'book_id': int(book_id), 'average_rating': 0, 'review_count': 0})

        average = round(float(result[0].get('average_rating') or 0), 2)
        count = int(result[0].get('review_count') or 0)
        return Response({'book_id': int(book_id), 'average_rating': average, 'review_count': count})


class BooksSummaryAveragesView(APIView):
    """
    GET /api/reviews/books/summary/averages/
    Returns list of averages for all books with at least one review:
    [{"book_id": 1, "average_rating": 4.5, "review_count": 3}, ...]
    """

    def get(self, request):
        ensure_indexes()
        pipeline = [
            {'$match': {'status': ACTIVE_STATUS}},
            {
                '$group': {
                    '_id': '$book_id',
                    'average_rating': {'$avg': '$rating'},
                    'review_count': {'$sum': 1},
                }
            },
            {'$sort': {'_id': 1}},
        ]
        qs = list(get_reviews_collection().aggregate(pipeline))
        payload = [
            {
                'book_id': int(row['_id']),
                'average_rating': round(float(row['average_rating']), 2),
                'review_count': row['review_count'],
            }
            for row in qs
        ]
        return Response(payload)
