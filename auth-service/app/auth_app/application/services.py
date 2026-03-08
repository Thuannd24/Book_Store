from auth_app.infrastructure.orm_models import TokenBlacklist


class TokenService:
    @staticmethod
    def is_blacklisted(jti: str) -> bool:
        return TokenBlacklist.objects.filter(jti=jti).exists()
