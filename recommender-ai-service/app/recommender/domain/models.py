from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BookRecommendation:
    book_id: int
    title: str
    score: Optional[float]
    reason: str
    average_rating: float
    category_id: Optional[int]
