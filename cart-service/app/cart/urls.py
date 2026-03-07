from django.urls import path
from .views import (
    health,
    CartByCustomerView,
    CartItemsView,
    CartItemDetailView,
    ClearCartView,
)

urlpatterns = [
    path('health/', health, name='health'),
    # Cart read
    path('carts/customer/<int:customer_id>/', CartByCustomerView.as_view(), name='cart-by-customer'),
    # Cart items
    path('carts/customer/<int:customer_id>/items/', CartItemsView.as_view(), name='cart-items'),
    path('carts/items/<int:item_id>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    # Clear cart
    path('carts/customer/<int:customer_id>/clear/', ClearCartView.as_view(), name='cart-clear'),
]
