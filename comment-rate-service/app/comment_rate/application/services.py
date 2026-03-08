from comment_rate.infrastructure.orm_models import Review
from django.db.models import Avg, Count


class ReviewService:
    @staticmethod
    def get_by_book(book_id: int):
        return Review.objects.filter(book_id=book_id, status=Review.Status.ACTIVE)

    @staticmethod
    def get_by_customer(customer_id: int):
        return Review.objects.filter(customer_id=customer_id, status=Review.Status.ACTIVE)

    @staticmethod
    def get_average(book_id: int):
        agg = Review.objects.filter(book_id=book_id, status=Review.Status.ACTIVE).aggregate(
            average_rating=Avg('rating'), review_count=Count('id')
        )
        return agg['average_rating'] or 0, agg['review_count'] or 0

    @staticmethod
    def get_all_averages():
        return (
            Review.objects.filter(status=Review.Status.ACTIVE)
            .values('book_id')
            .annotate(average_rating=Avg('rating'), review_count=Count('id'))
        )
