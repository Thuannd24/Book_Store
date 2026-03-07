from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = [
            'id',
            'book_id',
            'book_title_snapshot',
            'price_snapshot',
            'quantity',
            'subtotal',
        ]
        read_only_fields = ['id', 'book_title_snapshot', 'price_snapshot', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'customer_id',
            'status',
            'total_items',
            'total_amount',
            'created_at',
            'updated_at',
            'items',
        ]
        read_only_fields = fields


class AddItemSerializer(serializers.Serializer):
    """Request body for POST /api/carts/customer/{customer_id}/items/"""
    book_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateItemSerializer(serializers.Serializer):
    """Request body for PUT /api/carts/items/{item_id}/"""
    quantity = serializers.IntegerField(min_value=1)


class CartForOrderSerializer(serializers.ModelSerializer):
    """
    Internal contract consumed by order-service.
    GET /internal/carts/customer/{customer_id}/for-order/
    """
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'customer_id',
            'status',
            'total_items',
            'total_amount',
            'items',
        ]
        read_only_fields = fields
