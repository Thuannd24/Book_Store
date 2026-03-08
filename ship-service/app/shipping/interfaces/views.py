from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from shipping.infrastructure.orm_models import Shipment
from shipping.infrastructure.serializers import ShipmentSerializer, InternalShipmentSerializer


@api_view(['GET'])
def health(request):
    db_ok = True
    try:
        from django.db import connection
        connection.ensure_connection()
    except Exception:
        db_ok = False
    return Response({
        'status': 'ok' if db_ok else 'degraded',
        'service': 'ship-service',
        'db': 'ok' if db_ok else 'error',
        'version': '2.0.0',
    }, status=200 if db_ok else 503)


def _generate_tracking(order_id: int, seq: int) -> str:
    return f"TRK-{order_id}-{seq:03d}"


def _next_sequence(order_id: int) -> int:
    last = Shipment.objects.filter(order_id=order_id).order_by('-id').first()
    return (last.id + 1) if last else 1


class InternalShipmentCreateView(APIView):
    """
    POST /internal/shipments/
    Body: {order_id, customer_id, shipping_method, shipping_address, shipping_fee}
    """

    def post(self, request):
        required = ['order_id', 'customer_id', 'shipping_method', 'shipping_address', 'shipping_fee']
        for field in required:
            if field not in request.data:
                return Response({'success': False, 'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

        order_id = int(request.data['order_id'])
        customer_id = int(request.data['customer_id'])
        shipping_method = request.data['shipping_method']
        shipping_address = request.data['shipping_address']
        shipping_fee = Decimal(str(request.data['shipping_fee']))

        if shipping_method not in Shipment.Method.values:
            return Response({'success': False, 'error': 'Invalid shipping_method'}, status=status.HTTP_400_BAD_REQUEST)

        tracking_code = _generate_tracking(order_id, _next_sequence(order_id))

        shipment = Shipment.objects.create(
            order_id=order_id,
            customer_id=customer_id,
            shipping_method=shipping_method,
            shipping_address=shipping_address,
            shipping_fee=shipping_fee,
            status=Shipment.Status.PENDING,
            tracking_code=tracking_code,
        )

        payload = InternalShipmentSerializer(shipment).data
        return Response({'success': True, 'shipment': payload}, status=status.HTTP_201_CREATED)


class InternalShipmentCancelView(APIView):
    """
    DELETE /internal/shipments/{shipment_id}/
    Cancels a shipment (saga compensation).
    """

    def delete(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(pk=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'success': False, 'error': 'Shipment not found.'}, status=status.HTTP_404_NOT_FOUND)

        shipment.status = Shipment.Status.FAILED
        shipment.save(update_fields=['status'])
        return Response({'success': True, 'shipment_id': shipment_id}, status=status.HTTP_200_OK)


class ShipmentDetailView(APIView):
    """
    GET /api/shipments/{shipment_id}/
    """

    def get(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(pk=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'detail': 'Shipment not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ShipmentSerializer(shipment).data)


class ShipmentByOrderView(APIView):
    """
    GET /api/shipments/order/{order_id}/
    """

    def get(self, request, order_id):
        shipments = Shipment.objects.filter(order_id=order_id)
        return Response(ShipmentSerializer(shipments, many=True).data)
