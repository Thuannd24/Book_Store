from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Shipment:
    order_id: int
    customer_id: int
    shipping_method: str
    shipping_address: str
    shipping_fee: Decimal
    status: str = 'PENDING'
    tracking_code: str = ''
