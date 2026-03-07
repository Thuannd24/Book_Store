from django.urls import path

from .views import RecommendationView, health

urlpatterns = [
    path('health/', health, name='health'),
    path('recommendations/customer/<int:customer_id>/', RecommendationView.as_view(), name='recommendations-customer'),
]
