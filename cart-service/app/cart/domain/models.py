from dataclasses import dataclass, field
from decimal import Decimal
from typing import List


@dataclass
class CartItem:
    book_id: int
    book_title_snapshot: str
    price_snapshot: Decimal
    quantity: int
    subtotal: Decimal = Decimal('0.00')


@dataclass
class Cart:
    customer_id: int
    status: str = 'ACTIVE'
    total_items: int = 0
    total_amount: Decimal = Decimal('0.00')
    items: List[CartItem] = field(default_factory=list)
