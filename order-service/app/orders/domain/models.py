from dataclasses import dataclass, field
from decimal import Decimal
from typing import List


@dataclass
class OrderItem:
    book_id: int
    book_title_snapshot: str
    price_snapshot: Decimal
    quantity: int
    subtotal: Decimal


@dataclass
class Order:
    customer_id: int
    cart_id: int
    payment_method: str
    shipping_method: str
    shipping_address: str
    total_amount: Decimal
    items: List[OrderItem] = field(default_factory=list)
    status: str = 'PENDING'
    payment_status: str = 'PENDING'
    shipping_status: str = 'PENDING'
