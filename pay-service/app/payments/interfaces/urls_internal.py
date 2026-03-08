from django.urls import path

from payments.interfaces.views import InternalPaymentCreateView, InternalPaymentCancelView

urlpatterns = [
    path('payments/', InternalPaymentCreateView.as_view(), name='internal-payment-create'),
    path('payments/<int:payment_id>/', InternalPaymentCancelView.as_view(), name='internal-payment-cancel'),
]
