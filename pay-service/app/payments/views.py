from datetime import datetime
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentSerializer, InternalPaymentSerializer


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'pay-service'})


def _generate_tx_ref(order_id: int, seq: int) -> str:
    return f"PAY-{order_id}-{seq:03d}"


def _next_sequence(order_id: int) -> int:
    last = Payment.objects.filter(order_id=order_id).order_by('-id').first()
    return (last.id + 1) if last else 1


class InternalPaymentCreateView(APIView):
    """
    POST /internal/payments/
    Body: {order_id, customer_id, method, amount}
    Contracted response for order-service and others.
    """

    def post(self, request):
        required_fields = ['order_id', 'customer_id', 'method', 'amount']
        for field in required_fields:
            if field not in request.data:
                return Response({'success': False, 'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

        method = request.data['method']
        amount = Decimal(str(request.data['amount']))
        order_id = int(request.data['order_id'])
        customer_id = int(request.data['customer_id'])

        if method not in Payment.Method.values:
            return Response({'success': False, 'error': 'Invalid payment method'}, status=status.HTTP_400_BAD_REQUEST)

        # Simple academic rule: COD -> PENDING, BANK_TRANSFER -> SUCCESS
        status_value = Payment.Status.PENDING if method == Payment.Method.COD else Payment.Status.SUCCESS
        tx_ref = _generate_tx_ref(order_id, _next_sequence(order_id))

        payment = Payment.objects.create(
            order_id=order_id,
            customer_id=customer_id,
            method=method,
            amount=amount,
            status=status_value,
            transaction_ref=tx_ref,
            paid_at=datetime.utcnow() if status_value == Payment.Status.SUCCESS else None,
        )

        payload = InternalPaymentSerializer(payment).data
        return Response({'success': True, 'payment': payload}, status=status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    """
    GET /api/payments/{payment_id}/
    """

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaymentSerializer(payment).data)


class PaymentByOrderView(APIView):
    """
    GET /api/payments/order/{order_id}/
    """

    def get(self, request, order_id):
        payments = Payment.objects.filter(order_id=order_id)
        return Response(PaymentSerializer(payments, many=True).data)
