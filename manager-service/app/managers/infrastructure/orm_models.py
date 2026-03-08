from django.db import models
from django.utils import timezone


class Manager(models.Model):
    manager_code = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'managers'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.full_name} ({self.manager_code})"
