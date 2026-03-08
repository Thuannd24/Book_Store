from django.db import models


class TokenBlacklist(models.Model):
    """Tracks blacklisted refresh tokens (logout)."""
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    token = models.TextField()
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'token_blacklist_custom'

    def __str__(self):
        return f'BlacklistedToken(jti={self.jti})'
