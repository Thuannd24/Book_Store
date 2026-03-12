from decimal import Decimal
from collections import defaultdict

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import connection

from orders.infrastructure.orm_models import Order, OrderItem, PromoCode
from orders.infrastructure.serializers import OrderSerializer, CreateOrderSerializer
from orders.application.services import OrderSaga


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
            promo_code=data.get('promo_code') or None,
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


class CustomerPromoListView(APIView):
    """
    GET /api/customers/{customer_id}/promos/
    Returns all promo codes for a customer that are still usable (UNUSED or RETURNED).
    """

    def get(self, request, customer_id):
        promos = PromoCode.objects.filter(
            customer_id=customer_id,
            status__in=[PromoCode.Status.UNUSED, PromoCode.Status.RETURNED],
        ).order_by('-created_at')

        data = [
            {
                'code': p.code,
                'percentage': str(p.percentage),
                'max_discount_amount': str(p.max_discount_amount),
                'status': p.status,
                'valid_from': p.valid_from,
                'valid_to': p.valid_to,
            }
            for p in promos
        ]
        return Response({'customer_id': customer_id, 'promos': data})

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
            order.save(update_fields=['status', 'shipping_status'])
        elif new_status == 'DELIVERED':
            order.shipping_status = 'DELIVERED'

            from django.db import transaction

            with transaction.atomic():
                order.save(update_fields=['status', 'shipping_status'])

                # Mark applied promo as USED when order is fully delivered
                if order.promo_code:
                    try:
                        promo = PromoCode.objects.select_for_update().get(
                            code=order.promo_code,
                            customer_id=order.customer_id,
                        )
                    except PromoCode.DoesNotExist:
                        promo = None

                    if promo and promo.status in [PromoCode.Status.RESERVED, PromoCode.Status.UNUSED, PromoCode.Status.RETURNED]:
                        promo.status = PromoCode.Status.USED
                        promo.applied_order_id = order.id
                        promo.save(update_fields=['status', 'applied_order_id'])

                # Issue new promo codes based on delivered order count
                delivered_count = Order.objects.filter(
                    customer_id=order.customer_id,
                    shipping_status='DELIVERED',
                ).count()

                promo_to_create = None
                if delivered_count == 1:
                    promo_to_create = {'percentage': 5, 'max_discount': 30000}
                elif delivered_count == 5:
                    promo_to_create = {'percentage': 10, 'max_discount': 50000}
                elif delivered_count == 10:
                    promo_to_create = {'percentage': 15, 'max_discount': 100000}
                elif delivered_count == 20:
                    promo_to_create = {'percentage': 20, 'max_discount': 200000}
                elif delivered_count >= 20 and delivered_count % 10 == 0:
                    promo_to_create = {'percentage': 20, 'max_discount': 200000}

                if promo_to_create:
                    from decimal import Decimal
                    import uuid

                    PromoCode.objects.create(
                        code=str(uuid.uuid4()).replace('-', '').upper()[:16],
                        customer_id=order.customer_id,
                        percentage=Decimal(str(promo_to_create['percentage'])),
                        max_discount_amount=Decimal(str(promo_to_create['max_discount'])),
                        status=PromoCode.Status.UNUSED,
                    )
        else:
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
