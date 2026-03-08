from .orm_models import Book
from django.db.models import Q


class BookRepository:
    def get_by_id(self, book_id: int):
        try:
            return Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return None

    def get_all(self, category_id=None, keyword=None):
        qs = Book.objects.all()
        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(author__icontains=keyword))
        return qs

    def save(self, book):
        book.save()
        return book

    def delete(self, book):
        book.delete()
