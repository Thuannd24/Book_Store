from django.urls import include, path

urlpatterns = [
    path('api/', include('shipping.urls')),
    path('internal/', include('shipping.urls_internal')),
]
