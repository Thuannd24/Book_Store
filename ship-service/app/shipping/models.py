from decimal import Decimal
from django.db import models


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        READY_TO_SHIP = 'READY_TO_SHIP', 'Ready to Ship'
        SHIPPING = 'SHIPPING', 'Shipping'
        DELIVERED = 'DELIVERED', 'Delivered'
        FAILED = 'FAILED', 'Failed'

    class Method(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard'
        EXPRESS = 'EXPRESS', 'Express'

    order_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(db_index=True)
    shipping_method = models.CharField(max_length=20, choices=Method.choices)
    shipping_address = models.TextField()
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    tracking_code = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shipments'
        ordering = ['-created_at']

    def __str__(self):
        return f'Shipment(id={self.id}, order_id={self.order_id}, status={self.status})'
