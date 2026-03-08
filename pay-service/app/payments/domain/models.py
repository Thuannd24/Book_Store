from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Payment:
    order_id: int
    customer_id: int
    method: str
    amount: Decimal
    status: str = 'PENDING'
    transaction_ref: str = ''
    paid_at: Optional[object] = None
