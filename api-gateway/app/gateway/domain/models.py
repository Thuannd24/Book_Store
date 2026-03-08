from dataclasses import dataclass
from typing import Optional


@dataclass
class ProxyRequest:
    method: str
    service_key: str
    path_suffix: str
    user_id: Optional[int] = None
    role: Optional[str] = None
