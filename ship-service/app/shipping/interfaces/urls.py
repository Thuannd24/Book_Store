from django.urls import path

from shipping.interfaces.views import health, ShipmentDetailView, ShipmentByOrderView

urlpatterns = [
    path('health/', health, name='health'),
    path('shipments/<int:shipment_id>/', ShipmentDetailView.as_view(), name='shipment-detail'),
    path('shipments/order/<int:order_id>/', ShipmentByOrderView.as_view(), name='shipment-by-order'),
]
