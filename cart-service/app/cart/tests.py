from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from cart.models import Cart, CartItem


MOCK_BOOK = {
    'id': 1,
    'title': 'Clean Code',
    'price': '120.00',
    'stock': 10,
    'status': 'ACTIVE',
    'category_id': 2,
    'category_name_snapshot': 'Software Engineering',
}


class AutoCreateCartTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/internal/carts/auto-create/'

    def test_auto_create_success(self):
        response = self.client.post(self.url, {'customer_id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_id'], 1)
        self.assertEqual(Cart.objects.count(), 1)

    def test_auto_create_idempotent(self):
        """Calling twice must NOT create a second cart."""
        self.client.post(self.url, {'customer_id': 1}, format='json')
        response = self.client.post(self.url, {'customer_id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cart.objects.count(), 1)

    def test_auto_create_missing_customer_id(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CartByCustomerTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cart = Cart.objects.create(customer_id=42)

    def test_get_cart(self):
        response = self.client.get('/api/carts/customer/42/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_id'], 42)
        self.assertEqual(response.data['items'], [])

    def test_get_cart_auto_creates_if_missing(self):
        response = self.client.get('/api/carts/customer/999/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_id'], 999)


class AddItemTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cart = Cart.objects.create(customer_id=10)
        self.url = '/api/carts/customer/10/items/'

    @patch('cart.interfaces.views.get_book_detail')
    def test_add_item_success(self, mock_book):
        mock_book.return_value = {'success': True, 'book': MOCK_BOOK}
        response = self.client.post(self.url, {'book_id': 1, 'quantity': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(Decimal(response.data['total_amount']), Decimal('240.00'))
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['book_title_snapshot'], 'Clean Code')

    @patch('cart.interfaces.views.get_book_detail')
    def test_add_same_book_increments_quantity(self, mock_book):
        mock_book.return_value = {'success': True, 'book': MOCK_BOOK}
        self.client.post(self.url, {'book_id': 1, 'quantity': 1}, format='json')
        response = self.client.post(self.url, {'book_id': 1, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(response.data['total_items'], 4)

    @patch('cart.interfaces.views.get_book_detail')
    def test_add_item_book_service_down(self, mock_book):
        mock_book.return_value = {'success': False, 'error': 'book-service is unreachable'}
        response = self.client.post(self.url, {'book_id': 99, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @patch('cart.interfaces.views.get_book_detail')
    def test_add_item_out_of_stock(self, mock_book):
        book = {**MOCK_BOOK, 'stock': 0, 'status': 'OUT_OF_STOCK'}
        mock_book.return_value = {'success': True, 'book': book}
        response = self.client.post(self.url, {'book_id': 1, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_invalid_quantity(self):
        response = self.client.post(self.url, {'book_id': 1, 'quantity': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateRemoveItemTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cart = Cart.objects.create(customer_id=20)
        self.item = CartItem.objects.create(
            cart=self.cart,
            book_id=1,
            book_title_snapshot='Clean Code',
            price_snapshot=Decimal('120.00'),
            quantity=2,
        )
        self.cart.recompute_totals()

    def test_update_item_quantity(self):
        response = self.client.put(
            f'/api/carts/items/{self.item.id}/',
            {'quantity': 5},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 5)
        self.assertEqual(Decimal(response.data['total_amount']), Decimal('600.00'))

    def test_update_item_not_found(self):
        response = self.client.put('/api/carts/items/99999/', {'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_item(self):
        response = self.client.delete(f'/api/carts/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(CartItem.objects.count(), 0)


class ClearCartTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cart = Cart.objects.create(customer_id=30)
        CartItem.objects.create(
            cart=self.cart,
            book_id=1,
            book_title_snapshot='Book A',
            price_snapshot=Decimal('50.00'),
            quantity=3,
        )
        self.cart.recompute_totals()

    def test_clear_cart(self):
        response = self.client.delete('/api/carts/customer/30/clear/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(Decimal(response.data['total_amount']), Decimal('0.00'))
        self.assertEqual(CartItem.objects.count(), 0)

    def test_clear_cart_not_found(self):
        response = self.client.delete('/api/carts/customer/99999/clear/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartForOrderTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cart = Cart.objects.create(customer_id=50)
        CartItem.objects.create(
            cart=self.cart,
            book_id=1,
            book_title_snapshot='Clean Code',
            price_snapshot=Decimal('120.00'),
            quantity=1,
        )
        self.cart.recompute_totals()

    def test_for_order_returns_cart_with_items(self):
        response = self.client.get('/internal/carts/customer/50/for-order/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 1)

    def test_for_order_empty_cart_returns_400(self):
        Cart.objects.create(customer_id=51)
        response = self.client.get('/internal/carts/customer/51/for-order/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_for_order_not_found(self):
        response = self.client.get('/internal/carts/customer/99999/for-order/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HealthTest(TestCase):
    def test_health(self):
        response = APIClient().get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
