from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Shipment


class InternalShipmentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/internal/shipments/'
        self.payload = {
            "order_id": 100,
            "customer_id": 1,
            "shipping_method": "STANDARD",
            "shipping_address": "Ha Noi",
            "shipping_fee": "20.00",
        }

    def test_create_shipment(self):
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        shipment = Shipment.objects.get()
        self.assertEqual(shipment.status, Shipment.Status.PENDING)
        self.assertTrue(shipment.tracking_code.startswith('TRK-100-'))

    def test_invalid_method(self):
        payload = {**self.payload, "shipping_method": "FAST"}
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PublicShipmentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.shipment = Shipment.objects.create(
            order_id=200,
            customer_id=2,
            shipping_method=Shipment.Method.STANDARD,
            shipping_address="123 Street",
            shipping_fee=Decimal('10.00'),
            status=Shipment.Status.PENDING,
            tracking_code="TRK-200-001",
        )

    def test_get_shipment_detail(self):
        res = self.client.get(f'/api/shipments/{self.shipment.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['order_id'], 200)

    def test_get_shipments_by_order(self):
        res = self.client.get('/api/shipments/order/200/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['tracking_code'], 'TRK-200-001')
