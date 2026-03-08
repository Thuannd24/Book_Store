from decimal import Decimal

from django.db import models


class Book(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        OUT_OF_STOCK = 'OUT_OF_STOCK', 'Out of Stock'
        INACTIVE = 'INACTIVE', 'Inactive'

    title = models.CharField(max_length=255)
    isbn = models.CharField(max_length=32, unique=True)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    category_id = models.IntegerField(null=True, blank=True)
    category_name_snapshot = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'books'
        ordering = ['id']

    def __str__(self):
        return f'Book(id={self.id}, title={self.title})'

    def mark_out_of_stock_if_needed(self):
        """Ensure status aligns with stock levels."""
        if self.stock == 0 and self.status == Book.Status.ACTIVE:
            self.status = Book.Status.OUT_OF_STOCK

    def save(self, *args, **kwargs):
        self.price = Decimal(self.price)
        self.mark_out_of_stock_if_needed()
        super().save(*args, **kwargs)
