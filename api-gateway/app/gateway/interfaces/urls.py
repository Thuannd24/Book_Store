from django.urls import path, re_path

from gateway.interfaces.views import ProxyView, AuthProxyView, health, metrics, circuit_breaker_status

urlpatterns = [
    path('health/', health, name='health'),
    path('metrics/', metrics, name='metrics'),
    path('circuit-breakers/', circuit_breaker_status, name='circuit-breaker-status'),
    re_path(r'^gateway/auth/(?P<path_suffix>.*)$', AuthProxyView.as_view(), name='gateway-auth-proxy'),
    re_path(r'^gateway/(?P<service_key>[a-zA-Z0-9_-]+)/(?P<path_suffix>.*)$', ProxyView.as_view(), name='gateway-proxy'),
]
