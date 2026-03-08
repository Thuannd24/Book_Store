from dataclasses import dataclass


@dataclass
class Staff:
    staff_code: str
    full_name: str
    email: str
    role: str
    department: str = ''
    is_active: bool = True
