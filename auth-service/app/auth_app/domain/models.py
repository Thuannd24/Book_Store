from dataclasses import dataclass


@dataclass
class AuthToken:
    access: str
    refresh: str
    user_id: int
    email: str
    role: str
