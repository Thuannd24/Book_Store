import logging
from books.infrastructure.orm_models import Book

logger = logging.getLogger(__name__)


class BookService:
    @staticmethod
    def get_book(book_id: int):
        try:
            return Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return None

    @staticmethod
    def get_all(category_id=None, keyword=None):
        from django.db.models import Q
        qs = Book.objects.all()
        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(author__icontains=keyword))
        return qs

    @staticmethod
    def decrement_stock(items: list):
        """Decrement stock for a list of items: [{'book_id': 1, 'quantity': 2}, ...]"""
        from django.db import transaction
        with transaction.atomic():
            for item in items:
                book_id = item.get('book_id')
                quantity = item.get('quantity', 0)
                try:
                    book = Book.objects.select_for_update().get(pk=book_id)
                    book.stock -= quantity
                    book.save(update_fields=['stock'])
                    logger.info('Stock decremented for book %s by %d', book_id, quantity)
                except Book.DoesNotExist:
                    logger.error('Book %s not found for stock decrement.', book_id)
                except Exception as exc:
                    logger.error('Failed to decrement stock for book %s: %s', book_id, exc)
