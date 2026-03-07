from django.urls import path
from .views import (
    health,
    CustomerListView,
    RegisterView,
    LoginView,
    CustomerDetailView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/register/', RegisterView.as_view(), name='customer-register'),
    path('customers/login/', LoginView.as_view(), name='customer-login'),
    path('customers/<int:customer_id>/', CustomerDetailView.as_view(), name='customer-detail'),
]
