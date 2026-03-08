from django.urls import path

from .views import (
    health,
    OrderCreateView,
    OrderDetailView,
    OrderByCustomerView,
    OrderStatusUpdateView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('orders/customer/<int:customer_id>/', OrderByCustomerView.as_view(), name='orders-by-customer'),
]
