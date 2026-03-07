from django.urls import path

from .views import InternalPaymentCreateView

urlpatterns = [
    path('payments/', InternalPaymentCreateView.as_view(), name='internal-payment-create'),
]
