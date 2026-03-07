from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book
from .serializers import BookSerializer, InternalBookSerializer


# --- Health -----------------------------------------------------

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'book-service'})


# --- Public API -------------------------------------------------

class BookListCreateView(APIView):
    """
    GET  /api/books/?category_id=...&keyword=...
    POST /api/books/
    """

    def get(self, request):
        qs = Book.objects.all()
        category_id = request.query_params.get('category_id')
        keyword = request.query_params.get('keyword')

        if category_id is not None:
            qs = qs.filter(category_id=category_id)
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(author__icontains=keyword))

        serializer = BookSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailView(APIView):
    """
    GET    /api/books/{book_id}/
    PUT    /api/books/{book_id}/
    DELETE /api/books/{book_id}/
    """

    def _get_book(self, book_id):
        try:
            return Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return None

    def get(self, request, book_id):
        book = self._get_book(book_id)
        if book is None:
            return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BookSerializer(book).data)

    def put(self, request, book_id):
        book = self._get_book(book_id)
        if book is None:
            return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, book_id):
        book = self._get_book(book_id)
        if book is None:
            return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Internal API ----------------------------------------------

class InternalBookDetailView(APIView):
    """
    GET /internal/books/{book_id}/
    Returns contract consumed by cart-service.
    """

    def get(self, request, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return Response({'success': False, 'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        payload = InternalBookSerializer(book).data
        return Response({'success': True, 'book': payload})
