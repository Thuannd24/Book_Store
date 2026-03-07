from django.urls import path

from .views import PurchaseHistoryView

urlpatterns = [
    path('orders/customer/<int:customer_id>/history/', PurchaseHistoryView.as_view(), name='order-history'),
]
