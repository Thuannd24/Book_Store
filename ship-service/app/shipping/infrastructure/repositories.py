from .orm_models import Shipment


class ShipmentRepository:
    def get_by_id(self, shipment_id: int):
        try:
            return Shipment.objects.get(pk=shipment_id)
        except Shipment.DoesNotExist:
            return None

    def get_by_order(self, order_id: int):
        return Shipment.objects.filter(order_id=order_id)

    def save(self, shipment):
        shipment.save()
        return shipment
