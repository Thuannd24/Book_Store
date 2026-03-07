from django.urls import path, re_path

from .views import ProxyView, health

urlpatterns = [
    path('health/', health, name='health'),
    re_path(r'^gateway/(?P<service_key>[a-zA-Z0-9_-]+)/(?P<path_suffix>.*)$', ProxyView.as_view(), name='gateway-proxy'),
]
