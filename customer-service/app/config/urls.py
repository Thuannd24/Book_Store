from django.urls import path, include
from customers.interfaces.views import InternalCustomerDetailView

urlpatterns = [
    # Public API — mounted at /api/
    path('api/', include('customers.interfaces.urls')),

    # Internal API — consumed by other services only
    path('internal/customers/<int:customer_id>/', InternalCustomerDetailView.as_view(), name='internal-customer-detail'),
]
