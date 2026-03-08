# Application layer — use-case orchestration for cart operations.
# HTTP client logic is in infrastructure/repositories.py.
from cart.infrastructure.repositories import get_book_detail  # noqa: F401 — re-exported for use in views
