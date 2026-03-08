from django.urls import include, path

urlpatterns = [
    path('api/', include('orders.interfaces.urls')),
    path('internal/', include('orders.interfaces.urls_internal')),
]
