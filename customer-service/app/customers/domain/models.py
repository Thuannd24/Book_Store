from dataclasses import dataclass


@dataclass
class Customer:
    full_name: str
    email: str
    phone: str = ''
    address: str = ''
    is_active: bool = True
