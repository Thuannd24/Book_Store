from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Book:
    title: str
    isbn: str
    author: str
    publisher: str
    price: Decimal
    stock: int
    description: str = ''
    image_url: str = ''
    category_id: int = None
    category_name_snapshot: str = ''
    status: str = 'ACTIVE'
