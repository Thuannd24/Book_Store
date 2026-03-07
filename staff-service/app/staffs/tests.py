from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Staff


class StaffAuthTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/staff/register/'
        self.login_url = '/api/staff/login/'
        self.staff_data = {
            "staff_code": "S001",
            "full_name": "Alice Admin",
            "email": "alice@example.com",
            "password": "secret123",
            "role": "admin",
            "department": "IT",
        }

    def test_register_success(self):
        res = self.client.post(self.register_url, self.staff_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['email'], 'alice@example.com')
        self.assertEqual(Staff.objects.count(), 1)

    def test_register_duplicate_email(self):
        self.client.post(self.register_url, self.staff_data, format='json')
        res = self.client.post(self.register_url, self.staff_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        Staff.objects.create(
            staff_code="S001",
            full_name="Alice Admin",
            email="alice@example.com",
            password_hash=make_password("secret123"),
            role="admin",
            department="IT",
        )
        res = self.client.post(self.login_url, {"email": "alice@example.com", "password": "secret123"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['staff_code'], 'S001')

    def test_login_invalid(self):
        res = self.client.post(self.login_url, {"email": "missing@example.com", "password": "x"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class StaffQueryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = Staff.objects.create(
            staff_code="S001",
            full_name="Alice Admin",
            email="alice@example.com",
            password_hash=make_password("secret123"),
            role="admin",
            department="IT",
        )

    def test_get_staff_detail(self):
        res = self.client.get(f'/api/staff/{self.staff.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['staff_code'], 'S001')

    def test_list_staff(self):
        res = self.client.get('/api/staff/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
