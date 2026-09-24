from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseEntity:
    """Base para entidades de domínio que possuem identidade própria."""

    id: Optional[int] = None
