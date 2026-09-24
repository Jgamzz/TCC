from dataclasses import dataclass
from typing import Optional

from app.entities.base_entity import BaseEntity


@dataclass
class CargoEntity(BaseEntity):
    name: str = ""
    is_active: bool = True
