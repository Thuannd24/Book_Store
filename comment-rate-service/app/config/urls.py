from django.urls import include, path

urlpatterns = [
    path('api/', include('comment_rate.interfaces.urls')),
]
