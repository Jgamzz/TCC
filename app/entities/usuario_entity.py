from dataclasses import dataclass
from typing import Optional

from app.entities.base_entity import BaseEntity


@dataclass
class UsuarioEntity(BaseEntity):
    username: str = ""
    name: str = ""
    is_active: bool = True
    cargo_id: Optional[int] = None

    def possui_cargo(self, cargo_id: int) -> bool:
        return self.cargo_id == cargo_id
