from django.urls import path

from .views import health, LoginView, TokenVerifyView, TokenRefreshView, LogoutView

urlpatterns = [
    path('health/', health, name='auth-health'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/verify/', TokenVerifyView.as_view(), name='auth-token-verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
]
