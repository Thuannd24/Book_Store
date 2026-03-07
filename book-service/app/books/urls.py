from django.urls import path

from .views import (
    health,
    BookListCreateView,
    BookDetailView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('books/', BookListCreateView.as_view(), name='book-list'),
    path('books/<int:book_id>/', BookDetailView.as_view(), name='book-detail'),
]
