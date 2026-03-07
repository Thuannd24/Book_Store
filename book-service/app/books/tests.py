from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Book


def sample_payload(**overrides):
    base = {
        'title': 'Clean Code',
        'isbn': '9780132350884',
        'author': 'Robert C. Martin',
        'publisher': 'Prentice Hall',
        'price': '120.00',
        'stock': 5,
        'description': 'A handbook of agile software craftsmanship.',
        'image_url': 'http://example.com/clean-code.jpg',
        'category_id': 2,
        'category_name_snapshot': 'Software Engineering',
        'status': Book.Status.ACTIVE,
    }
    base.update(overrides)
    return base


class BookApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_book_sets_out_of_stock_when_zero(self):
        payload = sample_payload(stock=0)
        res = self.client.post('/api/books/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['status'], Book.Status.OUT_OF_STOCK)

    def test_list_filter_by_category(self):
        Book.objects.create(**sample_payload(title='A', category_id=1, isbn='111'))
        Book.objects.create(**sample_payload(title='B', category_id=2, isbn='222'))
        res = self.client.get('/api/books/?category_id=1')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['category_id'], 1)

    def test_keyword_search_title_or_author(self):
        Book.objects.create(**sample_payload(title='Python Tricks', author='Dan Bader', isbn='333'))
        Book.objects.create(**sample_payload(title='Golang 101', author='Alex', isbn='444'))
        res = self.client.get('/api/books/?keyword=python')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertIn('Python', res.data[0]['title'])

    def test_update_book_rejects_negative_stock(self):
        book = Book.objects.create(**sample_payload())
        payload = sample_payload(stock=-1, isbn=book.isbn)
        res = self.client.put(f'/api/books/{book.id}/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_book(self):
        book = Book.objects.create(**sample_payload())
        res = self.client.delete(f'/api/books/{book.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_internal_contract(self):
        book = Book.objects.create(**sample_payload())
        res = self.client.get(f'/internal/books/{book.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['book']['id'], book.id)
        self.assertEqual(Decimal(res.data['book']['price']), Decimal('120.00'))
        self.assertEqual(res.data['book']['category_name_snapshot'], 'Software Engineering')

    def test_internal_not_found(self):
        res = self.client.get('/internal/books/999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res.data['success'])
