from .orm_models import Review


class ReviewRepository:
    def get_by_book(self, book_id: int):
        return Review.objects.filter(book_id=book_id)

    def get_by_customer(self, customer_id: int):
        return Review.objects.filter(customer_id=customer_id)

    def save(self, review):
        review.save()
        return review
