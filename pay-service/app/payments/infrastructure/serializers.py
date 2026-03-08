from rest_framework import serializers

from .orm_models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'customer_id',
            'method',
            'amount',
            'status',
            'transaction_ref',
            'paid_at',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'transaction_ref', 'paid_at', 'created_at']


class InternalPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'customer_id',
            'method',
            'amount',
            'status',
            'transaction_ref',
        ]
