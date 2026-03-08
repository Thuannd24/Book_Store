from decimal import Decimal

from django.db import models


class Cart(models.Model):
    """
    One cart per customer. Status: ACTIVE | CHECKED_OUT | ABANDONED.
    customer_id is a snapshot; no foreign key to customer-service.
    """

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
        ABANDONED = 'ABANDONED', 'Abandoned'

    customer_id = models.IntegerField(unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    total_items = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f'Cart(customer_id={self.customer_id}, status={self.status})'

    def recompute_totals(self):
        """Recompute total_items and total_amount from current cart_items."""
        items = self.items.all()
        self.total_items = sum(item.quantity for item in items)
        self.total_amount = sum((item.subtotal for item in items), Decimal('0.00'))
        self.save(update_fields=['total_items', 'total_amount', 'updated_at'])


class CartItem(models.Model):
    """
    A line item inside a cart.
    book_id, book_title_snapshot, price_snapshot are all snapshots
    captured at the moment the item was added; no foreign key to book-service.
    """

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField(db_index=True)
    book_title_snapshot = models.CharField(max_length=512)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')

    class Meta:
        db_table = 'cart_items'
        unique_together = [('cart', 'book_id')]

    def __str__(self):
        return f'CartItem(cart_id={self.cart_id}, book_id={self.book_id}, qty={self.quantity})'

    def save(self, *args, **kwargs):
        self.price_snapshot = Decimal(self.price_snapshot)
        self.subtotal = self.price_snapshot * self.quantity
        super().save(*args, **kwargs)
