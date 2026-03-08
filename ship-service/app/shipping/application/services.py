from shipping.infrastructure.orm_models import Shipment


class ShipmentService:
    @staticmethod
    def get_shipment(shipment_id: int):
        try:
            return Shipment.objects.get(pk=shipment_id)
        except Shipment.DoesNotExist:
            return None

    @staticmethod
    def get_by_order(order_id: int):
        return Shipment.objects.filter(order_id=order_id)
