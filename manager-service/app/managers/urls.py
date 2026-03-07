from django.urls import path

from .views import (
    DashboardSummaryView,
    ManagerDetailView,
    ManagerLoginView,
    ManagerRegisterView,
    health,
)

urlpatterns = [
    path('health/', health, name='health'),
    path('managers/register/', ManagerRegisterView.as_view(), name='manager-register'),
    path('managers/login/', ManagerLoginView.as_view(), name='manager-login'),
    path('managers/<int:manager_id>/', ManagerDetailView.as_view(), name='manager-detail'),
    path('manager/dashboard/summary/', DashboardSummaryView.as_view(), name='manager-dashboard-summary'),
]
