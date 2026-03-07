from django.urls import path

from .views import (
    health,
    ReviewCreateView,
    ReviewsByBookView,
    ReviewsByCustomerView,
    BookAverageView,
    BooksSummaryAveragesView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('reviews/', ReviewCreateView.as_view(), name='review-create'),
    path('reviews/book/<int:book_id>/', ReviewsByBookView.as_view(), name='reviews-by-book'),
    path('reviews/customer/<int:customer_id>/', ReviewsByCustomerView.as_view(), name='reviews-by-customer'),
    path('reviews/book/<int:book_id>/average/', BookAverageView.as_view(), name='reviews-book-average'),
    path('reviews/books/summary/averages/', BooksSummaryAveragesView.as_view(), name='reviews-books-summary-averages'),
]
