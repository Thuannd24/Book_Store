from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartForOrderSerializer,
    AddItemSerializer,
    UpdateItemSerializer,
)
from .services import get_book_detail


# --- Health -----------------------------------------------------

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'cart-service'})


# --- Helpers ----------------------------------------------------

def _get_or_create_cart(customer_id: int) -> Cart:
    """Return the customer's ACTIVE cart, creating it if it doesn't exist."""
    cart, _ = Cart.objects.get_or_create(
        customer_id=customer_id,
        defaults={'status': Cart.Status.ACTIVE},
    )
    return cart


# --- Internal: Auto-create cart --------------------------------

class AutoCreateCartView(APIView):
    """
    POST /internal/carts/auto-create/

    Called by customer-service after a new customer registers.
    Idempotent: if cart already exists for customer_id, returns the existing one.
    """

    def post(self, request):
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response(
                {'detail': 'customer_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            customer_id = int(customer_id)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'customer_id must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = _get_or_create_cart(customer_id)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


# --- Public API: Cart ------------------------------------------

class CartByCustomerView(APIView):
    """
    GET /api/carts/customer/{customer_id}/

    Retrieve the cart (with all items) for a given customer.
    Auto-creates the cart if it doesn't exist yet.
    """

    def get(self, request, customer_id):
        cart = _get_or_create_cart(customer_id)
        return Response(CartSerializer(cart).data)


class CartItemsView(APIView):
    """
    POST /api/carts/customer/{customer_id}/items/

    Add a book to the cart.
    - Validates the book via book-service GET /internal/books/{id}/
    - If book already in cart: increments quantity
    - If book is new: creates a new CartItem with snapshot data
    - Recomputes cart totals after every change
    """

    def post(self, request, customer_id):
        serializer = AddItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book_id = serializer.validated_data['book_id']
        quantity = serializer.validated_data['quantity']

        # Validate book via book-service
        result = get_book_detail(book_id)
        if not result['success']:
            return Response(
                {'detail': result['error']},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        book = result['book']
        if book.get('status') != 'ACTIVE':
            return Response(
                {'detail': f"Book '{book.get('title')}' is not available for purchase."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if book.get('stock', 0) <= 0:
            return Response(
                {'detail': f"Book '{book.get('title')}' is out of stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            cart = _get_or_create_cart(customer_id)

            existing = cart.items.filter(book_id=book_id).first()
            if existing:
                existing.quantity += quantity
                existing.save()  # triggers subtotal recompute in save()
            else:
                price = Decimal(str(book['price']))
                CartItem.objects.create(
                    cart=cart,
                    book_id=book_id,
                    book_title_snapshot=book['title'],
                    price_snapshot=price,
                    quantity=quantity,
                )

            cart.recompute_totals()

        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


# --- Public API: Cart Items ------------------------------------

class CartItemDetailView(APIView):
    """
    PUT    /api/carts/items/{item_id}/  - update quantity
    DELETE /api/carts/items/{item_id}/  - remove item
    """

    def _get_item(self, item_id):
        try:
            return CartItem.objects.select_related('cart').get(pk=item_id)
        except CartItem.DoesNotExist:
            return None

    def put(self, request, item_id):
        item = self._get_item(item_id)
        if item is None:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            item.quantity = serializer.validated_data['quantity']
            item.save()  # triggers subtotal recompute
            item.cart.recompute_totals()

        return Response(CartSerializer(item.cart).data)

    def delete(self, request, item_id):
        item = self._get_item(item_id)
        if item is None:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            cart = item.cart
            item.delete()
            cart.recompute_totals()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class ClearCartView(APIView):
    """
    DELETE /api/carts/customer/{customer_id}/clear/

    Removes all items from the cart and resets totals to zero.
    """

    def delete(self, request, customer_id):
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({'detail': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            cart.items.all().delete()
            cart.total_items = 0
            cart.total_amount = Decimal('0.00')
            cart.save(update_fields=['total_items', 'total_amount', 'updated_at'])

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


# --- Internal: Cart for Order (order-service) ------------------

class CartForOrderView(APIView):
    """
    GET /internal/carts/customer/{customer_id}/for-order/

    Read-only snapshot of the cart used by order-service during checkout.
    Returns the frozen CartForOrderSerializer contract.
    """

    def get(self, request, customer_id):
        try:
            cart = Cart.objects.prefetch_related('items').get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({'detail': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        if cart.total_items == 0:
            return Response(
                {'detail': 'Cart is empty. Cannot create an order from an empty cart.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(CartForOrderSerializer(cart).data)
