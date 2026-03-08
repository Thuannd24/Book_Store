from decimal import Decimal
from collections import defaultdict

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import connection

from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from .saga import OrderSaga


@api_view(['GET'])
def health(request):
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False
    return Response({
        'status': 'ok' if db_ok else 'degraded',
        'service': 'order-service',
        'db': 'ok' if db_ok else 'error',
        'version': '2.0.0',
    }, status=200 if db_ok else 503)


class OrderCreateView(APIView):
    """
    GET  /api/orders/  — list all orders (manager dashboard)
    POST /api/orders/  — create an order from a customer's cart
    Body: {customer_id, payment_method, shipping_method, shipping_address, shipping_fee?}
    """

    def get(self, request):
        orders = Order.objects.prefetch_related('items').all()
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        saga = OrderSaga(
            customer_id=data['customer_id'],
            payment_method=data['payment_method'],
            shipping_method=data['shipping_method'],
            shipping_address=data['shipping_address'],
            shipping_fee=data.get('shipping_fee', '0.00'),
        )

        order, error, http_status = saga.run()

        if error:
            resp_data = {'detail': error}
            if order is not None:
                resp_data['order'] = OrderSerializer(order).data
            return Response(resp_data, status=http_status)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """
    GET /api/orders/{order_id}/
    """

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related('items').get(pk=order_id)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class OrderByCustomerView(APIView):
    """
    GET /api/orders/customer/{customer_id}/
    """

    def get(self, request, customer_id):
        orders = Order.objects.filter(customer_id=customer_id).prefetch_related('items')
        return Response(OrderSerializer(orders, many=True).data)


class OrderStatusUpdateView(APIView):
    """
    PATCH /api/orders/{order_id}/status/
    Body: { "status": "SHIPPING" } or { "status": "DELIVERED" }
    Allowed status transitions by staff:
      CONFIRMED → SHIPPING → DELIVERED
    """
    ALLOWED_TRANSITIONS = {
        'CONFIRMED': 'SHIPPING',
        'SHIPPING': 'DELIVERED',
    }

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status:
            return Response({'detail': 'status field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_next = self.ALLOWED_TRANSITIONS.get(order.status)
        if allowed_next is None:
            return Response(
                {'detail': f'Order status "{order.status}" cannot be advanced further.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_status != allowed_next:
            return Response(
                {'detail': f'Cannot transition from {order.status} to {new_status}. Expected: {allowed_next}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        if new_status == 'SHIPPING':
            order.shipping_status = 'SHIPPING'
        elif new_status == 'DELIVERED':
            order.shipping_status = 'DELIVERED'
        order.save(update_fields=['status', 'shipping_status'])

        return Response(OrderSerializer(order).data)


class PurchaseHistoryView(APIView):
    """
    GET /internal/orders/customer/{customer_id}/history/
    Returns aggregated purchase history for recommender service:
    {
      "customer_id": X,
      "books": [
        {"book_id": 1, "quantity": 3},
        ...
      ]
    }
    """

    def get(self, request, customer_id):
        items = OrderItem.objects.filter(order__customer_id=customer_id, order__status=Order.Status.CONFIRMED)
        aggregate = defaultdict(int)
        for item in items:
            aggregate[item.book_id] += item.quantity
        books = [{'book_id': bid, 'quantity': qty} for bid, qty in aggregate.items()]
        return Response({'customer_id': customer_id, 'books': books})
