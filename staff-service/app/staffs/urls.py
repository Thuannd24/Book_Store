from django.urls import path

from .views import (
    health,
    RegisterView,
    LoginView,
    StaffDetailView,
    StaffListView,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('staff/register/', RegisterView.as_view(), name='staff-register'),
    path('staff/login/', LoginView.as_view(), name='staff-login'),
    path('staff/<int:staff_id>/', StaffDetailView.as_view(), name='staff-detail'),
    path('staff/', StaffListView.as_view(), name='staff-list'),
]
