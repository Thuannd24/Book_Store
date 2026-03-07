from django.urls import include, path

urlpatterns = [
    path('api/', include('orders.urls')),
    path('internal/', include('orders.urls_internal')),
]
