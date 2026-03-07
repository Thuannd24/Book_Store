from decimal import Decimal
from collections import defaultdict

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from .services import (
    fetch_cart_for_order,
    clear_cart,
    create_payment,
    create_shipment,
)


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'order-service'})


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
        customer_id = data['customer_id']
        payment_method = data['payment_method']
        shipping_method = data['shipping_method']
        shipping_address = data['shipping_address']
        shipping_fee = Decimal(str(data.get('shipping_fee', '0.00')))

        # Fetch cart snapshot
        cart_resp = fetch_cart_for_order(customer_id)
        if not cart_resp['success']:
            return Response(
                {'detail': 'Unable to fetch cart.', 'error': cart_resp.get('error')},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        cart = cart_resp['data']
        items = cart.get('items', [])
        if not items:
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = Decimal(str(cart['total_amount'])) + shipping_fee

        with transaction.atomic():
            order = Order.objects.create(
                customer_id=customer_id,
                cart_id=cart['id'],
                status=Order.Status.CREATED,
                payment_method=payment_method,
                shipping_method=shipping_method,
                shipping_address=shipping_address,
                total_amount=total_amount,
                payment_status='PENDING',
                shipping_status='PENDING',
            )

            order_items = []
            for item in items:
                order_items.append(OrderItem(
                    order=order,
                    book_id=item['book_id'],
                    book_title_snapshot=item['book_title_snapshot'],
                    price_snapshot=Decimal(str(item['price_snapshot'])),
                    quantity=item['quantity'],
                    subtotal=Decimal(str(item['subtotal'])),
                ))
            OrderItem.objects.bulk_create(order_items)

            # Call payment
            pay_resp = create_payment(order.id, customer_id, payment_method, total_amount)
            if pay_resp['success']:
                order.status = Order.Status.PAYMENT_CREATED
                order.payment_status = 'CREATED'
            else:
                order.status = Order.Status.FAILED
                order.payment_status = 'FAILED'
                order.save()
                return Response(
                    {'detail': 'Payment creation failed', 'order': OrderSerializer(order).data, 'error': pay_resp.get('error')},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # Call shipment
            ship_resp = create_shipment(order.id, customer_id, shipping_method, shipping_address, shipping_fee)
            if ship_resp['success']:
                order.status = Order.Status.SHIPMENT_CREATED
                order.shipping_status = 'CREATED'
            else:
                order.status = Order.Status.FAILED
                order.shipping_status = 'FAILED'
                order.save()
                return Response(
                    {'detail': 'Shipment creation failed', 'order': OrderSerializer(order).data, 'error': ship_resp.get('error')},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            order.status = Order.Status.CONFIRMED
            order.save()

        # Clear cart (best-effort, outside atomic)
        clear_cart(customer_id)

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
