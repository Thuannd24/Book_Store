from django.urls import path

from .views import InternalShipmentCreateView

urlpatterns = [
    path('shipments/', InternalShipmentCreateView.as_view(), name='internal-shipment-create'),
]
