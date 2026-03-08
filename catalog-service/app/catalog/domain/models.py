from dataclasses import dataclass


@dataclass
class Category:
    name: str
    slug: str
    description: str = ''
    is_active: bool = True
