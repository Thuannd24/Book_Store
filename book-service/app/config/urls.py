from django.urls import include, path

from books.interfaces.views import InternalBookDetailView

urlpatterns = [
    path('api/', include('books.interfaces.urls')),
    path('internal/books/<int:book_id>/', InternalBookDetailView.as_view(), name='internal-book-detail'),
]
