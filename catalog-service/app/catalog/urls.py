from django.urls import path

from .views import (
    health,
    CategoryListCreateView,
    CategoryDetailView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('catalog/categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('catalog/categories/<int:category_id>/', CategoryDetailView.as_view(), name='category-detail'),
]
