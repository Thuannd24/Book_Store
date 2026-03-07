from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Manager


class ManagerAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = Manager.objects.create(
            manager_code='M001',
            full_name='Alice Manager',
            email='alice@example.com',
            password_hash=make_password('secret123'),
        )

    def test_register_manager(self):
        payload = {
            'manager_code': 'M002',
            'full_name': 'Bob Boss',
            'email': 'bob@example.com',
            'password': 'pass1234',
        }
        res = self.client.post('/api/managers/register/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', res.data)
        self.assertEqual(Manager.objects.count(), 2)

    def test_login_success(self):
        res = self.client.post(
            '/api/managers/login/',
            {'email': 'alice@example.com', 'password': 'secret123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'alice@example.com')

    def test_login_invalid_password(self):
        res = self.client.post(
            '/api/managers/login/',
            {'email': 'alice@example.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile(self):
        res = self.client.get(f'/api/managers/{self.manager.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['manager_code'], 'M001')


class DashboardSummaryTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('managers.services.get_reviews_count', return_value=(7, None))
    @patch('managers.services.get_orders_count', return_value=(12, None))
    @patch('managers.services.get_books_count', return_value=(3, None))
    @patch('managers.services.get_customers_count', return_value=(5, None))
    def test_dashboard_summary(self, mock_reviews, mock_orders, mock_books, mock_customers):
        res = self.client.get('/api/manager/dashboard/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_customers'], 5)
        self.assertEqual(res.data['total_books'], 3)
        self.assertEqual(res.data['total_orders'], 12)
        self.assertEqual(res.data['total_reviews'], 7)
