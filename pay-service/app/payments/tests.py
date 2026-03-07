from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Payment


class InternalPaymentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/internal/payments/'
        self.payload = {
            "order_id": 100,
            "customer_id": 1,
            "method": "COD",
            "amount": "240.00",
        }

    def test_create_cod_pending(self):
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        payment = Payment.objects.get()
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertIsNone(payment.paid_at)

    def test_create_bank_transfer_success(self):
        payload = {**self.payload, "method": "BANK_TRANSFER", "amount": "150.00"}
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        payment = Payment.objects.get()
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(Decimal(payment.amount), Decimal('150.00'))


class PublicPaymentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.payment = Payment.objects.create(
            order_id=200,
            customer_id=2,
            method=Payment.Method.COD,
            amount=Decimal('99.99'),
            status=Payment.Status.PENDING,
            transaction_ref='PAY-200-001',
        )

    def test_get_payment_detail(self):
        res = self.client.get(f'/api/payments/{self.payment.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['order_id'], 200)

    def test_get_payment_by_order(self):
        res = self.client.get('/api/payments/order/200/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['transaction_ref'], 'PAY-200-001')
