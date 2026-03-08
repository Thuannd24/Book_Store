from dataclasses import dataclass


@dataclass
class Review:
    book_id: int
    customer_id: int
    rating: int
    comment: str = ''
    status: str = 'ACTIVE'
