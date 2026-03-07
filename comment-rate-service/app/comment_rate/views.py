from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review
from .serializers import ReviewSerializer


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'comment-rate-service'})


class ReviewCreateView(APIView):
    """
    POST /api/reviews/
    """

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(status=Review.Status.ACTIVE)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewsByBookView(APIView):
    """
    GET /api/reviews/book/{book_id}/
    """

    def get(self, request, book_id):
        reviews = Review.objects.filter(book_id=book_id, status=Review.Status.ACTIVE)
        return Response(ReviewSerializer(reviews, many=True).data)


class ReviewsByCustomerView(APIView):
    """
    GET /api/reviews/customer/{customer_id}/
    """

    def get(self, request, customer_id):
        reviews = Review.objects.filter(customer_id=customer_id, status=Review.Status.ACTIVE)
        return Response(ReviewSerializer(reviews, many=True).data)


class BookAverageView(APIView):
    """
    GET /api/reviews/book/{book_id}/average/
    Returns: {"book_id": X, "average_rating": 4.5, "review_count": 3}
    """

    def get(self, request, book_id):
        agg = Review.objects.filter(book_id=book_id, status=Review.Status.ACTIVE).aggregate(
            average_rating=Avg('rating'), review_count=Count('id')
        )
        average = agg['average_rating'] or 0
        count = agg['review_count'] or 0
        return Response({'book_id': book_id, 'average_rating': round(average, 2), 'review_count': count})


class BooksSummaryAveragesView(APIView):
    """
    GET /api/reviews/books/summary/averages/
    Returns list of averages for all books with at least one review:
    [{"book_id": 1, "average_rating": 4.5, "review_count": 3}, ...]
    """

    def get(self, request):
        qs = (
            Review.objects.filter(status=Review.Status.ACTIVE)
            .values('book_id')
            .annotate(average_rating=Avg('rating'), review_count=Count('id'))
        )
        payload = [
            {
                'book_id': row['book_id'],
                'average_rating': round(row['average_rating'], 2),
                'review_count': row['review_count'],
            }
            for row in qs
        ]
        return Response(payload)
