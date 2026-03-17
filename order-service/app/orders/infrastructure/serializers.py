from rest_framework import serializers

from .orm_models import Order, OrderItem, PromoCode


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'book_id',
            'book_title_snapshot',
            'price_snapshot',
            'quantity',
            'subtotal',
        ]
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_id',
            'cart_id',
            'status',
            'payment_method',
            'shipping_method',
            'shipping_address',
            'total_amount',
            'payment_status',
            'shipping_status',
            'promo_code',
            'created_at',
            'items',
        ]
        read_only_fields = ['id', 'status', 'total_amount', 'payment_status', 'shipping_status', 'created_at', 'items']


class CreateOrderSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1)
    payment_method = serializers.ChoiceField(choices=['COD', 'BANK_TRANSFER'])
    shipping_method = serializers.ChoiceField(choices=['STANDARD', 'EXPRESS'])
    shipping_address = serializers.CharField(max_length=1024)
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default='0.00', min_value=0)
    promo_code = serializers.CharField(max_length=64, required=False, allow_blank=True)


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ['code', 'percentage', 'max_discount_amount', 'valid_from', 'valid_to']
