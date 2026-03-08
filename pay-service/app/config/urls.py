from django.urls import include, path

urlpatterns = [
    path('api/', include('payments.interfaces.urls')),
    path('internal/', include('payments.interfaces.urls_internal')),
]
