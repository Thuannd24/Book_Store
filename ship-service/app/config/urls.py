from django.urls import include, path

urlpatterns = [
    path('api/', include('shipping.interfaces.urls')),
    path('internal/', include('shipping.interfaces.urls_internal')),
]
