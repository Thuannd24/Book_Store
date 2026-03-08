from django.db import models


class Review(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        HIDDEN = 'HIDDEN', 'Hidden'

    book_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(db_index=True)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f'Review(book_id={self.book_id}, rating={self.rating})'
