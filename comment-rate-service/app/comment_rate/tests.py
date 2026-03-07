from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Review


class ReviewApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.create_url = '/api/reviews/'

    def test_create_review(self):
        payload = {"book_id": 1, "customer_id": 2, "rating": 5, "comment": "Great!"}
        res = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_rating_validation(self):
        payload = {"book_id": 1, "customer_id": 2, "rating": 6, "comment": "Oops"}
        res = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewQueryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Review.objects.create(book_id=1, customer_id=1, rating=4, comment='Good')
        Review.objects.create(book_id=1, customer_id=2, rating=5, comment='Great')
        Review.objects.create(book_id=2, customer_id=1, rating=3, comment='Ok')

    def test_reviews_by_book(self):
        res = self.client.get('/api/reviews/book/1/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_reviews_by_customer(self):
        res = self.client.get('/api/reviews/customer/1/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_average(self):
        res = self.client.get('/api/reviews/book/1/average/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['review_count'], 2)
        self.assertAlmostEqual(res.data['average_rating'], 4.5, places=2)

    def test_summary(self):
        res = self.client.get('/api/reviews/books/summary/averages/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
