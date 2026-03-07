from django.urls import include, path

from books.views import InternalBookDetailView

urlpatterns = [
    path('api/', include('books.urls')),
    path('internal/books/<int:book_id>/', InternalBookDetailView.as_view(), name='internal-book-detail'),
]
