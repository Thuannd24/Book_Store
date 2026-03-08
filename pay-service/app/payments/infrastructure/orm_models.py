from decimal import Decimal
from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        COD = 'COD', 'Cash on Delivery'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'

    order_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(db_index=True)
    method = models.CharField(max_length=20, choices=Method.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_ref = models.CharField(max_length=64, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment(id={self.id}, order_id={self.order_id}, status={self.status})'
