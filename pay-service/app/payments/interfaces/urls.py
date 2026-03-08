from django.urls import path

from payments.interfaces.views import (
    health,
    PaymentDetailView,
    PaymentByOrderView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('payments/<int:payment_id>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/order/<int:order_id>/', PaymentByOrderView.as_view(), name='payment-by-order'),
]
