from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category


class CategoryApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/catalog/categories/'

    def test_create_category(self):
        res = self.client.post(self.list_url, {'name': 'Software', 'description': 'SW books'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['slug'], 'software')
        self.assertEqual(Category.objects.count(), 1)

    def test_list_categories(self):
        Category.objects.create(name='SW', slug='sw')
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_get_category_detail(self):
        category = Category.objects.create(name='Data', slug='data')
        res = self.client.get(f'/api/catalog/categories/{category.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Data')

    def test_update_category(self):
        category = Category.objects.create(name='Old', slug='old')
        res = self.client.put(
            f'/api/catalog/categories/{category.id}/',
            {'name': 'New', 'description': 'updated', 'slug': ''},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['slug'], 'new')

    def test_delete_category(self):
        category = Category.objects.create(name='Temp', slug='temp')
        res = self.client.delete(f'/api/catalog/categories/{category.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)
