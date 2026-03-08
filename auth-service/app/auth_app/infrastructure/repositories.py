from .orm_models import TokenBlacklist


class TokenBlacklistRepository:
    def add(self, jti: str, token: str) -> TokenBlacklist:
        return TokenBlacklist.objects.create(jti=jti, token=token)

    def is_blacklisted(self, jti: str) -> bool:
        return TokenBlacklist.objects.filter(jti=jti).exists()
