from django.urls import path

from shipping.interfaces.views import InternalShipmentCreateView, InternalShipmentCancelView

urlpatterns = [
    path('shipments/', InternalShipmentCreateView.as_view(), name='internal-shipment-create'),
    path('shipments/<int:shipment_id>/', InternalShipmentCancelView.as_view(), name='internal-shipment-cancel'),
]
