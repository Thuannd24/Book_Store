from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class RecommendationViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('recommender.application.services.fetch_ratings')
    @patch('recommender.application.services.fetch_books')
    @patch('recommender.application.services.fetch_purchase_history')
    def test_recommendations_with_history(self, mock_history, mock_books, mock_ratings):
        mock_history.return_value = {'customer_id': 1, 'books': [{'book_id': 1, 'quantity': 2}]}
        mock_books.return_value = [
            {'id': 1, 'title': 'Bought', 'category_id': 10, 'stock': 5, 'status': 'ACTIVE'},
            {'id': 2, 'title': 'Same Cat High Rating', 'category_id': 10, 'stock': 3, 'status': 'ACTIVE'},
            {'id': 3, 'title': 'Other Cat', 'category_id': 20, 'stock': 4, 'status': 'ACTIVE'},
        ]
        mock_ratings.return_value = [
            {'book_id': 2, 'average_rating': 4.8, 'review_count': 10},
            {'book_id': 3, 'average_rating': 3.0, 'review_count': 2},
        ]

        res = self.client.get('/api/recommendations/customer/1/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(len(res.data['recommendations']), 2)
        self.assertEqual(res.data['recommendations'][0]['book_id'], 2)  # higher rating & same category

    @patch('recommender.application.services.fetch_ratings', return_value=[])
    @patch('recommender.application.services.fetch_books')
    @patch('recommender.application.services.fetch_purchase_history', return_value={'customer_id': 2, 'books': []})
    def test_empty_history_uses_rating_and_stock(self, mock_history, mock_books, mock_ratings):
        mock_books.return_value = [
            {'id': 5, 'title': 'Top Rated', 'category_id': 30, 'stock': 2, 'status': 'ACTIVE'},
            {'id': 6, 'title': 'Out of Stock', 'category_id': 30, 'stock': 0, 'status': 'ACTIVE'},
        ]
        mock_ratings.return_value = [{'book_id': 5, 'average_rating': 4.9, 'review_count': 20}]

        res = self.client.get('/api/recommendations/customer/2/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['recommendations']), 1)
        self.assertEqual(res.data['recommendations'][0]['book_id'], 5)

    @patch('recommender.application.services.fetch_purchase_history')
    def test_upstream_error_returns_502(self, mock_history):
        from recommender.application.services import ServiceError

        mock_history.side_effect = ServiceError("upstream error")

        res = self.client.get('/api/recommendations/customer/3/')
        self.assertEqual(res.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(res.data['success'])
