from dataclasses import dataclass


@dataclass
class Manager:
    manager_code: str
    full_name: str
    email: str
    is_active: bool = True
