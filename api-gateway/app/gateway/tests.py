from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class ProxyTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('gateway.views.requests.request')
    def test_proxy_forwards_and_returns_json(self, mock_request):
        mock_resp = type('obj', (), {})()
        mock_resp.status_code = 201
        mock_resp.headers = {'Content-Type': 'application/json'}
        mock_resp.json = lambda: {'ok': True}
        mock_request.return_value = mock_resp

        res = self.client.post('/api/gateway/customers/register/', {'email': 'a@b.com'}, format='json')

        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data['ok'])
        mock_request.assert_called_once()

    @patch('gateway.views.requests.request')
    def test_proxy_handles_upstream_error(self, mock_request):
        mock_request.side_effect = Exception("boom")

        res = self.client.get('/api/gateway/books/')
        self.assertEqual(res.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn('detail', res.data)
