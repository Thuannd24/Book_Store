from django.db import models


class Staff(models.Model):
    staff_code = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=50)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'staffs'
        ordering = ['-created_at']

    def __str__(self):
        return f'Staff(id={self.id}, email={self.email})'
