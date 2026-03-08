from rest_framework import serializers

from .orm_models import Shipment


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            'id',
            'order_id',
            'customer_id',
            'shipping_method',
            'shipping_address',
            'shipping_fee',
            'status',
            'tracking_code',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'tracking_code', 'created_at']


class InternalShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            'id',
            'order_id',
            'customer_id',
            'shipping_method',
            'shipping_address',
            'shipping_fee',
            'status',
            'tracking_code',
        ]
