from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from orders.infrastructure.orm_models import Order, OrderItem


MOCK_CART = {
    "id": 10,
    "customer_id": 1,
    "status": "ACTIVE",
    "total_items": 2,
    "total_amount": "200.00",
    "items": [
        {
            "id": 1,
            "book_id": 5,
            "book_title_snapshot": "Clean Code",
            "price_snapshot": "120.00",
            "quantity": 1,
            "subtotal": "120.00",
        },
        {
            "id": 2,
            "book_id": 6,
            "book_title_snapshot": "DDD",
            "price_snapshot": "80.00",
            "quantity": 1,
            "subtotal": "80.00",
        },
    ],
}


class OrderFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "customer_id": 1,
            "payment_method": "COD",
            "shipping_method": "STANDARD",
            "shipping_address": "123 Street",
            "shipping_fee": "0.00",
        }

    @patch('orders.application.services.publish_event')
    @patch('orders.application.services.clear_cart')
    @patch('orders.application.services.create_shipment')
    @patch('orders.application.services.create_payment')
    @patch('orders.application.services.fetch_cart_for_order')
    def test_create_order_success(self, mock_cart, mock_pay, mock_ship, mock_clear, mock_event):
        mock_cart.return_value = {"success": True, "data": MOCK_CART}
        mock_pay.return_value = {"success": True, "payment": {"id": 1}}
        mock_ship.return_value = {"success": True, "shipment": {"id": 1}}
        mock_clear.return_value = {"success": True}

        res = self.client.post('/api/orders/', self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.items.count(), 2)

    @patch('orders.application.services.publish_event')
    @patch('orders.application.services.create_payment')
    @patch('orders.application.services.fetch_cart_for_order')
    def test_create_order_payment_fail(self, mock_cart, mock_pay, mock_event):
        mock_cart.return_value = {"success": True, "data": MOCK_CART}
        mock_pay.return_value = {"success": False, "error": "pay failed"}

        res = self.client.post('/api/orders/', self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_502_BAD_GATEWAY)
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.FAILED)

    @patch('orders.application.services.publish_event')
    @patch('orders.application.services.cancel_payment')
    @patch('orders.application.services.create_shipment')
    @patch('orders.application.services.create_payment')
    @patch('orders.application.services.fetch_cart_for_order')
    def test_create_order_shipment_fail(self, mock_cart, mock_pay, mock_ship, mock_cancel, mock_event):
        mock_cart.return_value = {"success": True, "data": MOCK_CART}
        mock_pay.return_value = {"success": True, "payment": {"id": 1}}
        mock_ship.return_value = {"success": False, "error": "ship failed"}
        mock_cancel.return_value = {"success": True}

        res = self.client.post('/api/orders/', self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_502_BAD_GATEWAY)
        order = Order.objects.get()
        self.assertIn(order.status, [Order.Status.COMPENSATED, Order.Status.FAILED])


class OrderQueryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        order = Order.objects.create(
            customer_id=1,
            cart_id=10,
            status=Order.Status.CONFIRMED,
            payment_method='COD',
            shipping_method='STANDARD',
            shipping_address='123',
            total_amount=Decimal('200.00'),
        )
        OrderItem.objects.create(
            order=order,
            book_id=5,
            book_title_snapshot='Clean Code',
            price_snapshot=Decimal('120.00'),
            quantity=1,
            subtotal=Decimal('120.00'),
        )

    def test_get_order_detail(self):
        order = Order.objects.first()
        res = self.client.get(f'/api/orders/{order.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('items', res.data)

    def test_orders_by_customer(self):
        res = self.client.get('/api/orders/customer/1/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_purchase_history(self):
        res = self.client.get('/internal/orders/customer/1/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['customer_id'], 1)
        self.assertEqual(res.data['books'][0]['book_id'], 5)
