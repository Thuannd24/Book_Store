from django.urls import include, path

from cart.interfaces.views import AutoCreateCartView, CartForOrderView

urlpatterns = [
    # Public API mounted at /api/
    path('api/', include('cart.interfaces.urls')),

    # Internal endpoints consumed by other services
    path('internal/carts/auto-create/', AutoCreateCartView.as_view(), name='internal-cart-auto-create'),
    path('internal/carts/customer/<int:customer_id>/for-order/', CartForOrderView.as_view(), name='internal-cart-for-order'),
]
