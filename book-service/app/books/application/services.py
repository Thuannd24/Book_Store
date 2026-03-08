from books.infrastructure.orm_models import Book


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
