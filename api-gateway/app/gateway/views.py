import logging

import requests
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'api-gateway'})


SERVICE_MAP = {
    'customers': settings.CUSTOMER_SERVICE_URL,
    'books': settings.BOOK_SERVICE_URL,
    'carts': settings.CART_SERVICE_URL,
    'orders': settings.ORDER_SERVICE_URL,
    'reviews': settings.REVIEW_SERVICE_URL,
    'recommendations': settings.RECOMMENDER_SERVICE_URL,
    'catalog': settings.CATALOG_SERVICE_URL,
    'staff': settings.STAFF_SERVICE_URL,
    'managers': settings.MANAGER_SERVICE_URL,
}


class ProxyView(APIView):
    """
    Proxies any method to the mapped downstream service.
    """

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def _proxy(self, request, service_key, path_suffix):
        base_url = SERVICE_MAP.get(service_key)
        if not base_url:
            return Response({'detail': 'Unknown service'}, status=status.HTTP_400_BAD_REQUEST)

        target_url = f"{base_url.rstrip('/')}/{path_suffix}"

        try:
            resp = requests.request(
                method=request.method,
                url=target_url,
                params=request.GET,
                json=request.data if request.body else None,
                headers={
                    key: value
                    for key, value in request.headers.items()
                    if key.lower() in ('authorization', 'content-type')
                },
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.warning("Proxy error to %s: %s", target_url, exc)
            return Response({'detail': 'Upstream unavailable', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Unexpected proxy error to %s: %s", target_url, exc)
            return Response({'detail': 'Upstream unavailable', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = resp.json()
            return Response(data, status=resp.status_code)

        return HttpResponse(resp.content, status=resp.status_code, content_type=content_type or 'application/octet-stream')

    def get(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def post(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def put(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def patch(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)

    def delete(self, request, service_key, path_suffix):
        return self._proxy(request, service_key, path_suffix)
