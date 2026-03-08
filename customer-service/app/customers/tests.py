from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status

from customers.infrastructure.orm_models import Customer


class CustomerRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/customers/register/'
        self.valid_payload = {
            'full_name': 'Nguyen Van A',
            'email': 'vana@example.com',
            'password': 'secret123',
            'phone': '0901234567',
            'address': '123 Le Loi, HCM',
        }

    @patch('customers.interfaces.views.create_cart_for_customer')
    def test_register_success_cart_created(self, mock_cart):
        mock_cart.return_value = {'success': True}
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'vana@example.com')
        self.assertTrue(response.data['cart_created'])
        self.assertNotIn('password', response.data)
        self.assertNotIn('password_hash', response.data)
        mock_cart.assert_called_once()

    @patch('customers.interfaces.views.create_cart_for_customer')
    def test_register_success_cart_failed(self, mock_cart):
        """Customer is created even when cart-service is down."""
        mock_cart.return_value = {'success': False, 'error': 'cart-service is unreachable'}
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['cart_created'])
        self.assertIn('warning', response.data)
        self.assertEqual(Customer.objects.count(), 1)

    @patch('customers.interfaces.views.create_cart_for_customer')
    def test_register_duplicate_email(self, mock_cart):
        mock_cart.return_value = {'success': True}
        self.client.post(self.register_url, self.valid_payload, format='json')
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_missing_fields(self):
        response = self.client.post(self.register_url, {'email': 'x@x.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/customers/login/'
        import hashlib
        Customer.objects.create(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashlib.sha256(b'password123').hexdigest(),
            is_active=True,
        )

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {'email': 'test@example.com', 'password': 'password123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {'email': 'test@example.com', 'password': 'wrongpass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email(self):
        response = self.client.post(
            self.login_url,
            {'email': 'nobody@example.com', 'password': 'any'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerProfileTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            full_name='Tran Thi B',
            email='thi_b@example.com',
            password_hash='irrelevant',
            phone='0987654321',
            address='456 Nguyen Hue, HCM',
            is_active=True,
        )
        self.detail_url = f'/api/customers/{self.customer.id}/'

    def test_get_profile(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'thi_b@example.com')

    def test_get_profile_not_found(self):
        response = self.client.get('/api/customers/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_profile(self):
        response = self.client.put(
            self.detail_url,
            {'full_name': 'Tran Thi B Updated', 'phone': '0111222333'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Tran Thi B Updated')
        self.assertEqual(response.data['phone'], '0111222333')


class InternalCustomerTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            full_name='Le Van C',
            email='lvc@example.com',
            password_hash='irrelevant',
            is_active=True,
        )

    def test_internal_get_customer(self):
        response = self.client.get(f'/internal/customers/{self.customer.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.customer.id)

    def test_internal_not_found(self):
        response = self.client.get('/internal/customers/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HealthTest(TestCase):
    def test_health(self):
        client = APIClient()
        response = client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
