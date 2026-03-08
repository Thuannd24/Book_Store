from decimal import Decimal

from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CREATED = 'CREATED', 'Created'
        PAYMENT_CREATED = 'PAYMENT_CREATED', 'Payment Created'
        PAYMENT_RESERVED = 'PAYMENT_RESERVED', 'Payment Reserved'
        SHIPMENT_CREATED = 'SHIPMENT_CREATED', 'Shipment Created'
        SHIPMENT_RESERVED = 'SHIPMENT_RESERVED', 'Shipment Reserved'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FAILED = 'FAILED', 'Failed'
        COMPENSATING = 'COMPENSATING', 'Compensating'
        COMPENSATED = 'COMPENSATED', 'Compensated'

    customer_id = models.IntegerField(db_index=True)
    cart_id = models.IntegerField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CREATED)
    payment_method = models.CharField(max_length=32)
    shipping_method = models.CharField(max_length=32)
    shipping_address = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(max_length=32, blank=True, default='')
    shipping_status = models.CharField(max_length=32, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'Order(id={self.id}, customer_id={self.customer_id}, status={self.status})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField()
    book_title_snapshot = models.CharField(max_length=512)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'OrderItem(order_id={self.order_id}, book_id={self.book_id}, qty={self.quantity})'


class SagaLog(models.Model):
    order_id = models.IntegerField(db_index=True)
    step = models.CharField(max_length=64)
    status = models.CharField(max_length=32)  # STARTED, COMPLETED, FAILED, COMPENSATED
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saga_logs'
        ordering = ['created_at']

    def __str__(self):
        return f'SagaLog(order_id={self.order_id}, step={self.step}, status={self.status})'
